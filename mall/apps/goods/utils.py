# -*- encode: utf-8 -*-
# @Author: dsh
# Time: 2021/2/12 下午1:13
from .models import GoodsChannel


def get_breadcrumb(cat3):
    """包装面包屑导航数据"""
    cat1 = cat3.parent.parent
    cat1.url = GoodsChannel.objects.filter(category_id=cat1.id)[0].url
    breadcrumb = {
        'cat1': cat1,
        'cat2': cat3.parent,
        'cat3': cat3
    }
    return breadcrumb
