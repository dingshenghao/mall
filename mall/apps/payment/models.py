from django.db import models
from mall.utils.model import BaseModel


class Payment(BaseModel):
    """支付信息"""
    order_id = models.CharField(max_length=64, verbose_name='订单id')
    trade_id = models.CharField(max_length=100, unique=True, null=True, blank=True, verbose_name="支付编号")

    class Meta:
        db_table = 'tb_payment'
        verbose_name = '支付信息'
        verbose_name_plural = verbose_name
