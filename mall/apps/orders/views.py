import json
from decimal import Decimal
from datetime import datetime

from django.db import transaction
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django_redis import get_redis_connection
from django.http import HttpResponseForbidden, JsonResponse

from user.models import Address
from goods.models import SKU, SPU
from areas.models import Area
from .models import OrderInfo, OrderGoods
from mall.utils.response_code import RETCODE

import logging

logger = logging.getLogger('django')


@login_required(login_url='/login/')
def OrdersSettlement(request):
    user = request.user
    addresses = Address.objects.filter(user_id=user.id, is_deleted=False)
    for address in addresses:
        address.province = Area.objects.get(id=address.province_id).name
        address.city = Area.objects.get(id=address.city_id).name
        address.district = Area.objects.get(id=address.district_id).name
    # 地址为空，结算时跳转编辑页面
    addresses = addresses or None
    redis_coon = get_redis_connection('carts')
    sku_ids = redis_coon.hgetall('cart_%d' % user.id)
    selected_ids = redis_coon.smembers('selected_%d' % user.id)
    carts = {}
    for sku_id in selected_ids:
        carts[int(sku_id)] = int(sku_ids[sku_id])

    # 初始值
    total_count = 0  # 商品数量
    total_amount = Decimal('0.00')  # 商品总金额
    skus = SKU.objects.filter(id__in=carts.keys())
    for sku in skus:
        sku.count = carts[sku.id]
        sku.amount = sku.count * sku.price

        total_count += sku.count
        total_amount += sku.amount
    # 运费10元
    freight = Decimal('10.00')
    context = {
        'addresses': addresses,
        'skus': skus,
        'total_count': total_count,
        'total_amount': total_amount,
        'freight': freight,
        'payment_amount': total_amount + freight
    }
    return render(request, 'place_order.html', context)


@login_required(login_url='/login/')
def OrdersCommit(request):
    if request.method == 'POST':
        json_dict = json.loads(request.body.decode())
        address_id = json_dict.get('address_id')
        pay_method = json_dict.get('pay_method')
        if not all([address_id, pay_method]):
            return HttpResponseForbidden('缺少比传参数')
        try:
            address = Address.objects.get(id=address_id)
        except Exception as e:
            logger.error(e)
            return HttpResponseForbidden('address_id有误')
        try:
            pay_method = int(pay_method)
            if pay_method not in [OrderInfo.PAY_METHODS_ENUM['CASH'], OrderInfo.PAY_METHODS_ENUM['ALIPAY']]:
                return HttpResponseForbidden('支付方式有误')
        except Exception as e:
            logger.error(e)
            return HttpResponseForbidden('支付方式有误')
        user = request.user

        # 用户订单编号模式
        order_id = datetime.now().strftime('%Y%m%d%H%M%S') + ('%09d' % user.id)

        with transaction.atomic():  # 手动开启数据库事物

            try:

                # 创建事务保存点
                save_point = transaction.savepoint()

                order = OrderInfo.objects.create(
                    order_id=order_id,
                    user_id=user.id,
                    address_id=address_id,
                    total_count=0,
                    total_amount=Decimal('0.00'),
                    freight=Decimal('10.00'),
                    pay_method=pay_method,
                    status=OrderInfo.ORDER_STATUS_ENUM['UNPAID'] if pay_method == OrderInfo.PAY_METHODS_ENUM[
                        'ALIPAY'] else
                    OrderInfo.ORDER_STATUS_ENUM['UNSEND']
                )
                print(order)
                redis_coon = get_redis_connection('carts')
                sku_ids = redis_coon.hgetall('cart_%d' % user.id)
                selected_ids = redis_coon.smembers('selected_%d' % user.id)
                carts = {}
                for sku_id_bytes in selected_ids:
                    carts[int(sku_id_bytes)] = int(sku_ids[sku_id_bytes])
                skus_id = carts.keys()
                for sku_id in skus_id:
                    while True:  # 给用户无限次数的下单机会
                        sku = SKU.objects.get(id=sku_id)
                        buy_count = carts[sku_id]
                        # 修改sku销量与库存
                        origin_stock = sku.stock  # sku原库存
                        origin_sales = sku.sales  # sku原销量
                        # 判断购买数量是否大于库存
                        if buy_count > origin_stock:
                            transaction.savepoint_rollback(save_point)  # 下单失败，回滚到事物保存点
                            return JsonResponse({'code': RETCODE.STOCKERR, 'errmsg': '库存不足'})
                        # 购买成功，修改sku销量与库存
                        # sku.stock = origin_stock - buy_count
                        # sku.sales = origin_sales + buy_count
                        # sku.save()
                        # 使用乐观锁修改数据库
                        result = SKU.objects.filter(id=sku_id, stock=origin_stock).update(
                            stock=origin_stock - buy_count, sales=origin_sales + buy_count)
                        # 如果下单失败,给用户无限次下单机会,只到成功或库存不足
                        if result == 0:
                            continue
                        # 修改spu销量
                        spu = SPU.objects.get(id=sku.spu_id)
                        origin_sales = spu.sales
                        # spu.sales = buy_count + origin_sales
                        # spu.save()
                        # 使用乐观锁修改数据库
                        SPU.objects.filter(id=sku.spu_id).update(sales=buy_count + origin_sales)
                        # 保存订单
                        OrderGoods.objects.create(
                            order_id=order_id,
                            sku_id=sku_id,
                            count=buy_count,
                            price=sku.price
                        )
                        # 保存商品订单中总价和总数量
                        order.total_count += buy_count
                        order.total_amount += (buy_count * sku.price)
                        break
                order.total_amount += order.freight
                order.save()
            except Exception as e:
                logger.error(e)
                transaction.savepoint_rollback(save_point)  # 下单失败，回滚到事物保存点
                return JsonResponse({'code': RETCODE.STOCKERR, 'errmsg': '下单失败'})
            else:
                transaction.savepoint_commit(save_point)  # 提交事物
        # 提交订单后删除redis中的购物车数据
        pl = redis_coon.pipeline()
        pl.hdel('cart_%d' % user.id, *selected_ids)
        pl.srem('selected_%d' % user.id, *selected_ids)
        pl.execute()
        return JsonResponse({'code': RETCODE.OK, 'errmsg': '下单成功', 'order_id': order.order_id})


@login_required(login_url='/login/')
def OrdersSuccess(request):
    if request.method == 'GET':
        # http://www.tiantian.site:8000/orders/success/?order_id=20210214161631000000003&payment_amount=21295&pay_method=2
        order_id = request.GET.get('order_id')
        pay_method = request.GET.get('pay_method')
        payment_amount = request.GET.get('payment_amount')
        try:
            order_info = OrderInfo.objects.get(order_id=order_id, total_amount=payment_amount, pay_method=pay_method,
                                               user_id=request.user.id)
        except OrderInfo.DoesNotExist:
            return HttpResponseForbidden('参数错误')
        context = {
            'order_id': order_id,
            'pay_method': pay_method,
            'payment_amount': payment_amount,
        }
        return render(request, 'order_success.html', context)


@login_required(login_url='/login/')
def Order_Info(request):
    user = request.user
    # 用户订单
    page_orders = []
    orders_info = OrderInfo.objects.filter(user_id=user.id)
    for order_info in orders_info:
        # 订单商品
        sku_list = []
        orders_goods = OrderGoods.objects.filter(order_id=order_info.order_id)
        for order_goods in orders_goods:
            sku = SKU.objects.get(id=order_goods.sku_id)
            # 模型中如果没有这些字段，可以临时添加一些属性
            sku.count = order_goods.count
            sku.amount = sku.count * sku.price
            sku_list.append(sku)
            order_info.sku_list = sku_list
        # 支付方式
        order_info.pay_method_name = OrderInfo.PAY_METHOD_CHOICES[order_info.pay_method - 1][-1]
        # 订单状态
        order_info.status_name = OrderInfo.ORDER_STATUS_CHOICES[order_info.status - 1][1]
        page_orders.append(order_info)
    return render(request, 'user_center_order.html', {'page_orders': page_orders})


@login_required(login_url='/login/')
def GoodsComment(request):
    if request.method == 'GET':
        user_id = request.user.id
        order_id = request.GET.get('order_id')
        try:
            order_info = OrderInfo.objects.get(order_id=order_id, user_id=user_id, status=4)
        except OrderInfo.DoesNotExist:
            return HttpResponseForbidden('商品信息出现错误')
        goods_orders = OrderGoods.objects.filter(order_id=order_info.order_id)
        skus = []
        for goods_order in goods_orders:
            sku_id = goods_order.sku_id
            try:
                sku_model = SKU.objects.get(id=sku_id)
                sku = {
                    'order_id': goods_order.order_id,
                    'sku_id': sku_model.id,
                    'name': sku_model.name,
                    'price': str(sku_model.price),
                    'default_image_url': sku_model.default_image.url,
                    'score': goods_order.score,
                    'comment': goods_order.comment,
                    'is_anonymous': str(goods_order.is_anonymous)
                }
                skus.append(sku)
            except SKU.DoesNotExist:
                return HttpResponseForbidden('商品不存在')
    elif request.method == 'POST':
        user_id = request.user.id
        query_dict = json.loads(request.body.decode())
        order_id = query_dict['order_id']
        sku_id = query_dict['sku_id']
        comment = query_dict['comment']
        score = query_dict['score']
        is_anonymous = query_dict['is_anonymous']
        if not all([order_id, sku_id, comment]):
            return HttpResponseForbidden('缺少比传参数')
        if not isinstance(is_anonymous, bool):
            return HttpResponseForbidden('参数类型错误')
        try:
            goods_order_model = OrderGoods.objects.get(order_id=order_id, sku_id=sku_id)
            sku = SKU.objects.get(id=sku_id)
        except SKU.DoesNotExist:
            return HttpResponseForbidden('商品不存在')
        goods_order_model.comment = comment
        goods_order_model.score = score
        goods_order_model.is_anonymous = is_anonymous
        goods_order_model.is_commented = True
        sku.comments += 1
        sku.save()
        goods_order_model.save()
        goods_orders_model = OrderGoods.objects.filter(order_id=order_id)
        for goods_order in goods_orders_model:
            if goods_order.is_commented:
                pass
        OrderInfo.objects.filter(order_id=order_id, user_id=user_id).update(status=5)
        return JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK'})
    return render(request, 'goods_judge.html', {'skus': skus})
