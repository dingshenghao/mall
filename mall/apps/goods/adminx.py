# -*- encode: utf-8 -*-
# @Author: dsh
# Time: 2021/2/17 上午10:44

import xadmin
from xadmin import views

from goods import models


class SKUAdmin(object):
    """SKU模型站点管理类"""
    model_icon = 'fa fa-gift'
    # 在后台展示的字段
    list_display = ['id', 'name', 'price', 'stock', 'sales']


xadmin.site.register(models.GoodsCategory)
xadmin.site.register(models.GoodsChannel)
xadmin.site.register(models.SPU)
xadmin.site.register(models.Brand)
xadmin.site.register(models.SPUSpecification)
xadmin.site.register(models.SpecificationOption)
xadmin.site.register(models.SKU, SKUAdmin)
xadmin.site.register(models.SKUSpecification)
xadmin.site.register(models.SKUImage)


class BaseSetting(object):
    """xadmin的基本配置"""
    enable_themes = True  # 开启主题切换功能
    use_bootswatch = True  # 可以使用更多主题


xadmin.site.register(views.BaseAdminView, BaseSetting)


class GlobalSettings(object):
    """xadmin的全局配置"""
    site_title = "天天商城运营管理系统"  # 设置站点标题
    site_footer = "天天商城集团有限公司"  # 设置站点的⻚脚
    menu_style = "accordion"  # 设置菜单折叠


xadmin.site.register(views.CommAdminView, GlobalSettings)
