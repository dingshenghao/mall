# -*- encode: utf-8 -*-
# @Author: dsh
# Time: 2021/2/14 上午10:08
import pickle
import base64
from django_redis import get_redis_connection


def merge_cart_cookie_to_redis(request, response):
    """
    登录时合并购物车
    :param request: 登录时借用过来的请求对象
    :param response:借用过来准备做删除cookie的响应对象
    :return:
    """
    cart_str = request.COOKIES.get('carts')
    if cart_str:
        cart_dict = pickle.loads(base64.b64decode(cart_str.encode()))
    else:
        return
    redis_coon = get_redis_connection('carts')
    pl = redis_coon.pipeline()
    user = request.user
    for sku_id in cart_dict:
        pl.hset('cart_%d' % user.id, sku_id, cart_dict[sku_id]['count'])
        if cart_dict[sku_id]['selected']:
            pl.sadd('selected_%d' % user.id, sku_id)
        else:
            pl.srem('selected_%d' % user.id, sku_id)
    pl.execute()
    # 删除cookie中的购物车数据
    response.delete_cookie('carts')