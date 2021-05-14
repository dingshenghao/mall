# -*- encode: utf-8 -*-
# @Author: dsh
# Time: 2021/2/11 下午3:23
from goods.models import GoodsChannel, GoodsCategory


def get_categories():
    """
    获取商城商品分类菜单
    :return 菜单字典
    """
    categories = {}
    # 先按照group_id从小到大排序，当遇见相同的，再按照sequence排序
    goods_channel_qs = GoodsChannel.objects.order_by('group_id', 'sequence')
    for goods_channel in goods_channel_qs:
        group_id = goods_channel.group_id
        if group_id not in categories:
            categories[group_id] = {
                'channels': [],   # 一级
                'sub_cats': []    # 二级，二级中包含三级
            }
        cat1 = GoodsCategory.objects.get(id=goods_channel.category_id)
        cat1.url = goods_channel.url
        categories[group_id]['channels'].append(cat1)
        cat2s = GoodsCategory.objects.filter(parent_id=cat1.id)
        for cat2 in cat2s:
            cats3 = GoodsCategory.objects.filter(parent_id=cat2.id)
            cat2.sub_cats = cats3
            categories[group_id]['sub_cats'].append(cat2)
    return categories

