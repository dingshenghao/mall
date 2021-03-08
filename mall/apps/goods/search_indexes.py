# -*- encoding:UTF-8 -*-
# @Author: dsh
# Time: 2021/1/28 下午8:36
from haystack import indexes
from .models import SKU


class SKUIndex(indexes.SearchIndex, indexes.Indexable):
    """
    SKU索引数据模型类
    """
    text = indexes.CharField(document=True, use_template=True)

    def get_model(self):

        """返回建⽴索引的模型类"""
        return SKU

    def index_queryset(self, using=None):

        """返回要建⽴索引的数据查询集"""
        return self.get_model().objects.filter(is_launched=True)
