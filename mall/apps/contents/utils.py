# -*- encode: utf-8 -*-
# @Author: dsh
# Time: 2021/2/11 下午3:23
from goods.models import GoodsChannel, GoodsCategory


def get_categories():
    """
    获取商城商品分类菜单
    :return 菜单字典
    """
    # 商品频道及分类菜单
    # 使用有序字典保存类别的顺序
    # categories = {
    #     1: { # 组1
    #         'channels': [{'id':, 'name':, 'url':},{}, {}...],
    #         'sub_cats': [{'id':, 'name':, 'sub_cats':[{},{}]}, {}, {}, ..]
    #     },
    #     2: { # 组2
    #
    #     }
    # }
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
        # 查询出当前频道对应的一级类别
        cat1 = GoodsCategory.objects.get(id=goods_channel.category_id)
        # 给每个一级定义一个url属性来保存它自己的链接
        cat1.url = goods_channel.url
        # 将每个一级添加到channels一级列表中
        categories[group_id]['channels'].append(cat1)
        cat2s = GoodsCategory.objects.filter(parent_id=cat1.id)
        # 遍历二级查询结果集
        for cat2 in cat2s:
            # 查询出指定二级下面的所有三级
            cats3 = GoodsCategory.objects.filter(parent_id=cat2.id)
            # 将指定二级下的所有三级保存到二级的sub_cats的临时属性上
            cat2.sub_cats = cats3
            # 将每一个二级再添加到sub_cats对应的列表中
            categories[group_id]['sub_cats'].append(cat2)
    return categories

