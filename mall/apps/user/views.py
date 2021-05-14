import json
from random import randint
import re

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import check_password
from django.db import DatabaseError
from django.http import HttpResponse, JsonResponse, HttpResponseForbidden
from django.shortcuts import render, redirect
from django_redis import get_redis_connection
from django.contrib.auth import login, logout, authenticate
from itsdangerous import BadData

from celery_tasks.email.tasks import send_email
from celery_tasks.sms.tasks import send_message
from mall.libs.captcha.captcha import captcha
from mall.libs.yuntongxun.sms import CCP
from mall.settings.dev import EMAIL_VERIFY_URL
from mall.utils.response_code import RETCODE
from user import constants
from .models import User, Address
from areas.models import Area
from goods.models import SKU
from orders.utils import merge_cart_cookie_to_redis

import logging

from .utils import token_confirm

logger = logging.getLogger('django')


def Register(request):
    if request.method == 'POST':
        query_dict = request.POST.dict()
        username = query_dict.get('username')
        password = query_dict.get('password')
        password2 = query_dict.get('password2')
        mobile = query_dict.get('mobile')
        image_code = query_dict.get('image_code')
        sms_code = query_dict.get('sms_code')
        allow = query_dict.get('allow')
        if not all([username, password2, password, mobile, image_code, sms_code]):
            return HttpResponseForbidden('缺少比传参数')
        if allow is False:
            return HttpResponseForbidden('请勾选用户协议')
        if not re.match(r'^[a-zA-Z0-9_-]{5,20}$', username):
            return HttpResponseForbidden('请输入5-20个字符的用户名')
        if not re.match(r'^[0-9A-Za-z]{8,20}$', password):
            return HttpResponseForbidden('请输入8-20位的密码')
        if password != password2:
            return HttpResponseForbidden('输入两次密码不一致')
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return HttpResponseForbidden('请输入正确的手机号码')
        redis_coon = get_redis_connection('verify_code')
        sms_code_bytes = redis_coon.get(mobile)
        redis_coon.delete(mobile)
        if sms_code_bytes is None:
            return JsonResponse({'code': RETCODE.SMSCODERR, 'errmsg': '验证码已过期'})
        if sms_code != sms_code_bytes.decode():
            return JsonResponse({'code': RETCODE.SMSCODERR, 'errmsg': '验证码错误'})

        user = User.objects.create_user(username=username, password=password, mobile=mobile)
        login(request, user)
        response = redirect('/')
        response.set_cookie('username', user.username)
        return response
    return render(request, 'register.html')


# 图形验证码
def ImageCode(request, uuid):
    name, text, image_bytes = captcha.generate_captcha()
    redis_coon = get_redis_connection('verify_code')
    redis_coon.setex(uuid, constants.IMAGE_CODE_EXPIRE, text)
    # 将图形bytes数据响应给前端  # MIME
    return HttpResponse(image_bytes, content_type='image/png')


# 发送短信验证码
def SmsCode(request, mobile):
    redis_coon = get_redis_connection('verify_code')
    sms_flag_mobile = redis_coon.get('sms_flag_%s' % mobile)
    if sms_flag_mobile:
        return JsonResponse({'code': RETCODE.THROTTLINGERR, 'errmsg': '60s内只能发送一次'})

    query_dict = request.GET.dict()
    image_code = query_dict.get('image_code')
    uuid = query_dict.get('uuid')
    if not all([image_code, uuid]):
        return HttpResponseForbidden('缺少必传参数')
    image_code_bytes = redis_coon.get(uuid)
    redis_coon.delete(uuid)  # 验证码只能使用一次
    if image_code_bytes is None:
        return JsonResponse({'code': RETCODE.IMAGECODEERR, 'errmsg': '图形验证码已经过期'})
    if image_code.lower() != image_code_bytes.decode().lower():  # 将bytes类型转换为字符串，比且全部转为小写比较
        return JsonResponse({'code': RETCODE.IMAGECODEERR, 'errmsg': '图形验证码错误'})

    sms_code = '%06d' % randint(0, 999999)
    logger.info(sms_code)
    pl = redis_coon.pipeline()
    pl.setex(mobile, constants.SMS_CODE_EXPIRE, sms_code)
    # 发送过验证码的手机号设置一个标识
    pl.setex('sms_flag_%s' % mobile, constants.SEND_CODE_FLAG, 1)
    pl.execute()

    # 利用容联云发送短信
    # CCP().send_template_sms(mobile, [sms_code, 5], 1)
    # 使用celery异步发送短信
    send_message.delay(mobile, sms_code)
    return JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK'})


def check_username(request, username):
    if not re.match(r'^[a-zA-Z0-9_-]{5,20}$', username):
        return HttpResponseForbidden('请输入5-20个字符的用户名')
    count = User.objects.filter(username=username).count()
    data = {
        'count': count,
        'code': RETCODE.OK,
        'errmsg': 'ok'
    }
    print(data)
    return JsonResponse(data)


def check_mobile(request, mobile):
    if not re.match(r'^1[3-9]\d{9}$', mobile):
        return HttpResponseForbidden('请输入正确的手机号码')
    count = User.objects.filter(mobile=mobile).count()
    data = {
        'count': count,
        'code': RETCODE.OK,
        'errmsg': 'ok'
    }
    return JsonResponse(data)


def Login(request):
    if request.method == 'POST':
        query_dict = request.POST.dict()
        username = query_dict.get('username')
        password = query_dict.get('password')
        remembered = query_dict.get('remembered')
        if not all([username, password]):
            return HttpResponseForbidden('缺少比传参数')

        # 使用django自带的登录认证后端进行登录
        user = authenticate(request, username=username, password=password)
        if user is None:
            return render(request, 'login.html', {'account_errmsg': '用户名或密码错误'})
        login(request, user)
        if remembered is None:  # 如果不点记住登录，则设置session过期时间为0
            request.session.set_expiry(0)
        else:
            request.session.set_expiry(3600 * 24 * 7)  # 设置7天时间
        next = request.GET.get('next')
        response = redirect(next or '/')
        response.set_cookie('username', user.username)

        # 登录时合并购物车
        merge_cart_cookie_to_redis(request, response)

        return response
    return render(request, 'login.html')


def Logout(request):
    logout(request)
    response = redirect('user:login')
    response.delete_cookie('username')
    return response


def UserCenterInfo(request):
    user = request.user
    if user.is_authenticated:
        return render(request, 'user_center_info.html')
    else:
        return redirect('/login/?next=/info/')


@login_required(login_url='/login/')
def SendEmail(request):
    if request.method == 'PUT':
        json_dict = json.loads(request.body.decode())
        email = json_dict.get('email')
        if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return JsonResponse({'code': RETCODE.EMAILERR, 'errmsg': '邮箱格式错误'})
        user = request.user
        if user.email != email:
            user.email = email
            user.save()
        token = token_confirm.generate_validate_token(user.id)
        verify_url = EMAIL_VERIFY_URL + '?token=' + token
        # 使用celery异步发送邮件
        send_email.delay(email, verify_url)
        return JsonResponse({'code': RETCODE.OK, 'errmsg': '添加邮箱成功'})
    return redirect('user:info')


def EmailVerify(request):
    token = request.GET.get('token', None)
    if token is None:
        return HttpResponseForbidden('对不起，您的激活信息已过期，请重新发送激活链接激活!')
    try:
        user_id = token_confirm.confirm_validate_token(token)
        if not user_id:
            return HttpResponseForbidden('对不起，您的激活信息已过期，请重新发送激活链接激活!')
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return HttpResponseForbidden('对不起，您验证用户不存在，请重新注册!')
        user.email_active = True
        user.save()
        return redirect('user:info')
    except BadData:
        return HttpResponseForbidden('激活失败，请重新激活!')


@login_required(login_url='/login/')
def Password(request):
    if request.method == 'POST':
        query_dict = request.POST.dict()
        old_pwd = query_dict.get('old_pwd')
        new_pwd = query_dict.get('new_pwd')
        new_cpwd = query_dict.get('new_cpwd')
        if not all([old_pwd, new_pwd, new_cpwd]):
            return HttpResponseForbidden('缺少比传参数')
        if not re.match(r'^[0-9A-Za-z]{8,20}$', old_pwd):
            return HttpResponseForbidden('请输入8-20位的密码')
        if not re.match(r'^[0-9A-Za-z]{8,20}$', new_pwd):
            return HttpResponseForbidden('请输入8-20位的密码')
        if new_pwd == old_pwd:
            return render(request, 'user_center_pass.html', {'change_pwd_errmsg': '新旧密码一样，不能修改'})
        if new_pwd != new_cpwd:
            return JsonResponse({'code': RETCODE.CPWDERR, 'errmsg': '密码错误'})
        user = request.user
        if check_password(old_pwd, user.password) is False:
            return render(request, 'user_center_pass.html', {'change_pwd_errmsg': '原始密码错误'})
        try:
            user.set_password(new_pwd)
            user.save()
        except Exception as e:
            logger.error(e)
            return render(request, 'user_center_pass.html', {'change_pwd_errmsg': '修改密码失败'})
        logout(request)
        response = redirect('user:login')
        response.delete_cookie('username')
        return response
    return render(request, 'user_center_pass.html')


@login_required(login_url='/login/')
def Addresses(request):
    if request.method == 'GET':
        user = request.user
        addresses = Address.objects.filter(user_id=user.id, is_deleted=False)
        address_list = []
        for address in addresses:
            address_list.append({
                'id': address.id,
                'title': address.title,
                'receiver': address.receiver,
                'province_id': address.province_id,
                'province': Area.objects.get(id=address.province_id).name,
                'city_id': address.city_id,
                'city': Area.objects.get(id=address.city_id).name,
                'district_id': address.district_id,
                'district': Area.objects.get(id=address.district_id).name,
                'place': address.place,
                'mobile': address.mobile,
                'tel': address.tel,
                'email': address.email
            })
        context = {
            'addresses': address_list,
            'default_address_id': user.default_address_id
        }
        return render(request, 'user_center_site.html', context=context)


@login_required(login_url='/login/')
def AddressCreate(request):
    if request.method == 'POST':
        json_dict = json.loads(request.body.decode())
        title = json_dict.get('title')
        receiver = json_dict.get('receiver')
        province_id = json_dict.get('province_id')
        city_id = json_dict.get('city_id')
        district_id = json_dict.get('district_id')
        place = json_dict.get('place')
        mobile = json_dict.get('mobile')
        tel = json_dict.get('tel')
        email = json_dict.get('email')
        if all([title, receiver, province_id, city_id, district_id, place, mobile]) is False:
            return HttpResponseForbidden('缺少必传参数')
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return HttpResponseForbidden('手机号格式错误')
        if tel:
            if not re.match(r'^(0[0-9]{2,3}-)?([2-9][0-9]{6,7})+(-[0-9]{1,4})?$', tel):
                return HttpResponseForbidden('参数tel有误')
        if email:
            if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
                return HttpResponseForbidden('参数email有误')
        user = request.user
        try:
            address = Address.objects.create(
                user_id=user.id,
                title=title,
                receiver=receiver,
                province_id=province_id,
                city_id=city_id,
                district_id=district_id,
                place=place,
                mobile=mobile,
                tel=tel,
                email=email
            )
        except DatabaseError as e:
            logger.error(e)
            return HttpResponseForbidden('新增收货地址错误')
        if user.default_address_id is None:
            user.default_address_id = address.id
            user.save()
        address_dict = {
            'id': address.id,
            'title': address.title,
            'receiver': address.receiver,
            'province_id': address.province_id,
            'province': Area.objects.get(id=province_id).name,
            'city_id': address.city_id,
            'city': Area.objects.get(id=city_id).name,
            'district_id': address.district_id,
            'district': Area.objects.get(id=district_id).name,
            'place': address.place,
            'mobile': address.mobile,
            'tel': address.tel,
            'email': address.email
        }
        return JsonResponse({'code': RETCODE.OK, 'errmsg': '新增收货地址成功', 'address': address_dict})


@login_required(login_url='/login/')
def ChangeAddress(request, id):
    if request.method == 'PUT':
        user = request.user
        try:
            address = Address.objects.get(user_id=user.id, pk=id, is_deleted=False)
        except Address.DoesNotExist:
            return HttpResponseForbidden('id有误')
        json_dict = json.loads(request.body.decode())
        title = json_dict.get('title')
        receiver = json_dict.get('receiver')
        province_id = json_dict.get('province_id')
        city_id = json_dict.get('city_id')
        district_id = json_dict.get('district_id')
        place = json_dict.get('place')
        mobile = json_dict.get('mobile')
        tel = json_dict.get('tel')
        email = json_dict.get('email')
        if not all([title, receiver, province_id, city_id, district_id, place, mobile]):
            return HttpResponseForbidden('缺少比传参数')
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return HttpResponseForbidden('手机号格式错误')
        if tel:
            if not re.match(r'^(0[0-9]{2,3}-)?([2-9][0-9]{6,7})+(-[0-9]{1,4})?$', tel):
                return HttpResponseForbidden('参数tel有误')
        if email:
            if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
                return HttpResponseForbidden('参数email有误')
        address.title = title
        address.receiver = receiver
        address.province_id = province_id
        address.city_id = city_id
        address.district_id = district_id
        address.place = place
        address.mobile = mobile
        address.tel = tel
        address.email = email
        address.save()
        address_dict = {
            'id': address.id,
            'title': address.title,
            'receiver': address.receiver,
            'province_id': address.province_id,
            'province': Area.objects.get(id=province_id).name,
            'city_id': address.city_id,
            'city': Area.objects.get(id=city_id).name,
            'district_id': address.district_id,
            'district': Area.objects.get(id=district_id).name,
            'place': address.place,
            'mobile': address.mobile,
            'tel': address.tel,
            'email': address.email
        }
        return JsonResponse({'code': RETCODE.OK, 'errmsg': '修改收货地址成功', 'address': address_dict})
    elif request.method == 'DELETE':
        user = request.user
        try:
            address = Address.objects.get(pk=id, user_id=user.id, is_deleted=False)
        except Address.DoesNotExist:
            return HttpResponseForbidden('id有误')
        address.is_deleted = True
        address.save()
        return JsonResponse({'code': RETCODE.OK, 'errmsg': '删除地址成功'})


@login_required(login_url='/login/')
def ChangeAddressTitle(request):
    if request.method == 'PUT':
        user = request.user
        try:
            address = Address.objects.get(user_id=user.id, pk=id, is_deleted=False)
            json_dict = json.load(request.body.decode())
            title = json_dict.get('title')
            if title is None:
                return HttpResponseForbidden('请传入有效的标题')
            address.title = title
            address.save()
            return JsonResponse({'code': RETCODE.OK, 'errmsg': '修改标题成功'})
        except Exception as e:
            logger.error(e)
            return JsonResponse({'code': RETCODE.DBERR, 'errmsg': '修改标题失败'})


@login_required(login_url='/login/')
def ChangeDefaultAddress(request, id):
    if request.method == 'PUT':
        user = request.user
        try:
            address = Address.objects.get(pk=id, user_id=user.id, is_deleted=False)
            user.default_address_id = address.id
            user.save()
            return JsonResponse({'code': RETCODE.OK, 'errmsg': '设置默认收获地址成功'})
        except Exception as e:
            logger.error(e)
            return JsonResponse({'code': RETCODE.DBERR, 'errmsg': '设置默认收获地址失败'})


def BrowseHistory(request):
    if request.method == 'POST':
        """保存商品浏览记录"""
        user = request.user
        if not user.is_authenticated:
            return JsonResponse({'code': RETCODE.SESSIONERR, 'errmsg': '没有登录，不能保存浏览记录'})
        json_dict = json.loads(request.body.decode())
        sku_id = json_dict.get('sku_id')
        try:
            sku = SKU.objects.get(id=sku_id, is_launched=True)
        except SKU.DoesNotExist:
            return HttpResponseForbidden('sku_id不存在')
        redis_coon = get_redis_connection('history')
        pl = redis_coon.pipeline()
        # 先对列表进行去重
        pl.lrem('history_%d' % user.id, 0, sku_id)
        # 添加到列表中
        pl.lpush('history_%d' % user.id, sku_id)
        # 提取前5个元素
        pl.ltrim('history_%d' % user.id, 0, 4)
        pl.execute()
        return JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK'})
    if request.method == 'GET':
        """获取浏览记录"""
        user = request.user
        if not user.is_authenticated:
            return JsonResponse({'code': RETCODE.SESSIONERR, 'errmsg': '用户未登录，不能查看商品浏览记录'})
        redis_coon = get_redis_connection('history')
        sku_ids = redis_coon.lrange('history_%d' % user.id, 0, -1)
        sku_list = []
        for sku_id in sku_ids:
            sku = SKU.objects.get(id=sku_id)
            sku_list.append({
                'id': sku.id,
                'name': sku.name,
                'price': sku.price,
                'default_image_url': sku.default_image.url
            })
        return JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'skus': sku_list})