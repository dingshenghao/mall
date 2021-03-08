import json
import pickle
import base64
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import render
from django_redis import get_redis_connection

from goods.models import SKU

import logging

from mall.utils.response_code import RETCODE

logger = logging.getLogger('django')


def Carts(request):
    if request.method == 'POST':
        """添加购物车"""
        json_dict = json.loads(request.body.decode())
        sku_id = json_dict.get('sku_id')
        count = json_dict.get('count')
        selected = json_dict.get('selected', True)
        # 校验
        if not all([sku_id, count]):
            return HttpResponseForbidden('缺少必传参数')
        try:
            sku_model = SKU.objects.get(id=sku_id, is_launched=True)
        except SKU.DoesNotExist:
            return HttpResponseForbidden('sku_id不存在')
        try:
            count = int(count)
        except Exception as e:
            logger.info(e)
            return HttpResponseForbidden('参数类型错误')
        if isinstance(selected, bool) is False:
            return HttpResponseForbidden('参数类型错误')
        user = request.user
        if user.is_authenticated:
            """登录用户存储到redis中"""
            """
            hash: {sku_id_1: 1, sku_id_16: count}
            set: {sku_id_1, sku_id_16}
            """
            # 创建redis连接
            redis_coon = get_redis_connection('carts')
            pl = redis_coon.pipeline()
            # hincrby() 操作redis如果要添加的已存在，会自动做增量，不存在就是新增
            pl.hincrby('cart_%d' % user.id, sku_id, count)
            if selected:
                pl.sadd('selected_%d' % user.id, sku_id)
            pl.execute()
            return JsonResponse({'code': RETCODE.OK, 'errmsg': '添加购物车成功'})
        else:
            """未登录用户存储到cookie中"""
            """  
                {
                    sku_id_1: {'count': 1, 'selected': True}
                    sku_id_15: {'count': 1, 'selected': False}
                }
            """
            cart_str = request.COOKIES.get('carts')
            # 判断cookie中是否有数据
            if cart_str:
                cart_dict = pickle.loads(base64.b64decode(cart_str.encode()))
                if sku_id in cart_dict:  # 判断sku_id是否在字典中
                    cart_dict[sku_id]['count'] += count
                    cart_dict[sku_id]['selected'] = selected
            else:
                cart_dict = {}
            cart_dict[sku_id] = {'count': count, 'selected': selected}
            # 使用pickle和base64模块对字典加密
            cart_str = base64.b64encode(pickle.dumps(cart_dict)).decode()
            response = JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK'})
            response.set_cookie('carts', cart_str)
            return response
    elif request.method == 'GET':
        # 获取购物车数据
        user = request.user
        if user.is_authenticated:
            """获取redis中的购物车数据"""
            redis_coon = get_redis_connection('carts')
            sku_ids = redis_coon.hgetall('cart_%d' % user.id)
            selected_ids = redis_coon.smembers('selected_%d' % user.id)
            """  
                {
                    sku_id_1: {'count': 1, 'selected': True}
                    sku_id_15: {'count': 1, 'selected': False}
                }
            """
            cart_dict = {}
            for sku_id_bytes in sku_ids:
                cart_dict[int(sku_id_bytes)] = {
                    'count': int(sku_ids[sku_id_bytes]),
                    'selected': sku_id_bytes in selected_ids  # 判断sku_id是否存在与selected_ids集合中，存在返回True,否则返回False
                }
        else:
            """获取cookie中的数据"""
            cart_str = request.COOKIES.get('carts')
            if cart_str:
                # 将cookie中的字符串转换为字典
                cart_dict = pickle.loads(base64.b64decode(cart_str.encode()))
                pass
            else:
                # 如果没有从cookie获取数据，直接渲染空白页面
                return render(request, 'cart.html')
        sku_ids = SKU.objects.filter(id__in=cart_dict.keys())
        sku_list = []
        for sku in sku_ids:
            count = cart_dict[sku.id]['count']
            sku_list.append({
                'id': sku.id,
                'name': sku.name,
                'default_image_url': sku.default_image.url,
                'price': str(sku.price),
                'selected': str(cart_dict[sku.id]['selected']),
                'count': count,
                'amount': str(sku.price * count)
            })
        return render(request, 'cart.html', {'cart_skus': sku_list})
    elif request.method == 'PUT':
        # 更新购物车数据
        json_dict = json.loads(request.body.decode())
        sku_id = json_dict.get('sku_id')
        count = json_dict.get('count')
        selected = json_dict.get('selected')
        if not all([sku_id, count]):
            return HttpResponseForbidden('缺少比传参数')
        try:
            sku = SKU.objects.get(id=sku_id, is_launched=True)
        except SKU.DoesNotExist:
            return HttpResponseForbidden('sku_id不存在')
        try:
            count = int(count)
        except Exception as e:
            logger.info(e)
            return HttpResponseForbidden('参数类型错误')
        if isinstance(selected, bool) is False:
            return HttpResponseForbidden('参数类型错误')
        cart_sku = {
            'id': sku.id,
            'name': sku.name,
            'default_image_url': sku.default_image.url,
            'price': str(sku.price),
            'count': count,
            'selected': selected,
            'amount': str(count * sku.price)
        }
        response = JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'cart_sku': cart_sku})
        user = request.user
        if user.is_authenticated:
            """操作redis中的数据"""
            redis_coon = get_redis_connection('carts')
            redis_coon.hset('cart_%d' % user.id, sku_id, count)
            if selected:
                redis_coon.sadd('selected_%d' % user.id, sku_id)
            else:
                redis_coon.srem('selected_%d' % user.id, sku_id)
        else:
            """操作cookie中的数据"""
            cart_str = request.COOKIES.get('carts')
            if cart_str:
                cart_dict = pickle.loads(base64.b64decode(cart_str.encode()))
            else:
                return HttpResponseForbidden('没有cookie，谈何修改')
            cart_dict[sku_id] = {
                'count': count,
                'selected': selected
            }
            cart_str = base64.b64encode(pickle.dumps(cart_dict)).decode()
            response.set_cookie('carts', cart_str)
        return response
    elif request.method == 'DELETE':
        # 删除购物车商品
        json_dict = json.loads(request.body.decode())
        sku_id = json_dict.get('sku_id')
        if not all([sku_id]):
            return HttpResponseForbidden('缺少比传参数')
        try:
            sku = SKU.objects.get(id=sku_id, is_launched=True)
        except SKU.DoesNotExist:
            return HttpResponseForbidden('商品不存在')
        user = request.user
        if user.is_authenticated:
            redis_coon = get_redis_connection('carts')
            pl = redis_coon.pipeline()
            pl.hdel('cart_%d' % user.id, sku_id)
            pl.srem('selected_%d' % user.id, sku_id)
            pl.execute()
            return JsonResponse({'code': RETCODE.OK, 'errmsg': '删除成功'})
        else:
            cart_str = request.COOKIES.get('carts')
            if cart_str:
                cart_dict = pickle.loads(base64.b64decode(cart_str.encode()))
            else:
                return HttpResponseForbidden('没有cookie，无法删除')
            if sku_id in cart_dict.keys():
                del cart_dict[sku_id]
            # 创建响应对象
            response = JsonResponse({'code': RETCODE.OK, 'errmsg': '删除成功'})
            if not cart_dict:   # 如果字典中没有数据了，就将cookie删除
                response.delete_cookie('carts')
                return response
            cart_str = base64.b64encode(pickle.dumps(cart_dict)).decode()
            response.set_cookie('carts', cart_str)
            return response


def CartsSimple(request):
    if request.method == 'GET':
        user = request.user
        if user.is_authenticated:
            redis_coon = get_redis_connection('carts')
            sku_ids = redis_coon.hgetall('cart_%d' % user.id)
            selected_ids = redis_coon.smembers('selected_%d' % user.id)
            cart_dict = {}
            for sku_id_bytes in sku_ids:
                cart_dict[int(sku_id_bytes)] = {
                    'count': sku_ids[sku_id_bytes],
                    'selected': sku_id_bytes in selected_ids
                }
        else:
            cart_str = request.COOKIES.get('carts')
            if cart_str:
                cart_dict = pickle.loads(base64.b64decode(cart_str.encode()))
            else:
                cart_dict = {}
        # 查询sku模型
        sku_ids = SKU.objects.filter(id__in=cart_dict.keys())
        sku_list = []
        for sku in sku_ids:
            sku_list.append({
                'id': sku.id,
                'name': sku.name,
                'count': int(cart_dict[sku.id]['count']),
                'default_image_url': sku.default_image.url
            })
        return JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'cart_skus': sku_list})


def CartsSelection(request):
    if request.method == 'PUT':
        json_dict = json.loads(request.body.decode())
        selected = json_dict.get('selected')
        if isinstance(selected, bool) is False:
            return HttpResponseForbidden('参数类型错误')
        user = request.user
        if user.is_authenticated:
            redis_coon = get_redis_connection('carts')
            if selected:
                sku_ids = redis_coon.hgetall('cart_%d' % user.id)
                redis_coon.sadd('selected_%d' % user.id, *sku_ids.keys())
            else:
                redis_coon.delete('selected_%d' % user.id)
            return JsonResponse({'code': RETCODE.OK, 'errmsg': '全选成功'})
        else:
            cart_str = request.COOKIES.get('carts')
            if cart_str:
                cart_dict = pickle.loads(base64.b64decode(cart_str.encode()))
            else:
                return HttpResponseForbidden('没有cookie，无法全选')
            for sku_id in cart_dict:
                cart_dict[sku_id]['selected'] = selected
            cart_str = base64.b64encode(pickle.dumps(cart_dict)).decode()
            response = JsonResponse({'code': RETCODE.OK, 'errmsg': '全选成功'})
            response.set_cookie('carts', cart_str)
            return response