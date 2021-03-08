from django.db import models

from mall.utils.model import BaseModel


class GoodsCategory(BaseModel):
    """
    商品类别
    """
    name = models.CharField(max_length=10, verbose_name='名称')
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, verbose_name='父类别')

    class Meta:
        db_table = 'tb_goods_category'
        verbose_name = '商品类别'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


class GoodsChannelGroup(BaseModel):
    """商品频道组"""
    name = models.CharField(max_length=20, verbose_name='频道组名')

    class Meta:
        db_table = 'tb_channel_group'
        verbose_name = '商品频道组'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


class GoodsChannel(BaseModel):
    """商品频道"""
    group_id = models.IntegerField(verbose_name='频道id')
    category_id = models.IntegerField(verbose_name='商品类别id')
    url = models.CharField(max_length=50, verbose_name='频道页面链接')
    sequence = models.IntegerField(verbose_name='组内顺序')

    class Meta:
        db_table = 'tb_goods_channel'
        verbose_name = '商品频道'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.group_id


class Brand(BaseModel):
    """品牌"""
    name = models.CharField(max_length=20, verbose_name='名称')
    logo = models.ImageField(verbose_name='Logo图片')
    first_letter = models.CharField(max_length=1, verbose_name='品牌首字母')

    class Meta:
        db_table = 'tb_brand'
        verbose_name = '品牌'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


class SPU(BaseModel):
    """商品SPU"""
    name = models.CharField(max_length=50, verbose_name='名称')
    brand_id = models.IntegerField(verbose_name='品牌id')
    category1_id = models.IntegerField(verbose_name='一级类别id')
    category2_id = models.IntegerField(verbose_name='二级类别id')
    category3_id = models.IntegerField(verbose_name='三级类别id')
    sales = models.IntegerField(default=0, verbose_name='销量')
    comments = models.IntegerField(default=0, verbose_name='评价数')
    desc_detail = models.TextField(default='', verbose_name='详细介绍')
    desc_pack = models.TextField(default='', verbose_name='包装信息')
    desc_service = models.TextField(default='', verbose_name='售后服务')

    class Meta:
        db_table = 'tb_spu'
        verbose_name = '商品SPU'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


class SKU(BaseModel):
    """商品SKU"""
    name = models.CharField(max_length=50, verbose_name='名称')
    caption = models.CharField(max_length=100, verbose_name='副标题')
    spu_id = models.IntegerField(verbose_name='商品id')
    category_id = models.IntegerField(verbose_name='从属类别id')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='单价')
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='进价')
    market_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='市场价')
    stock = models.IntegerField(default=0, verbose_name='库存')
    sales = models.IntegerField(default=0, verbose_name='销量')
    comments = models.IntegerField(default=0, verbose_name='评价数')
    is_launched = models.BooleanField(default=True, verbose_name='是否上架销售')
    default_image = models.ImageField(max_length=200, default='', null=True, blank=True, verbose_name='默认图片')

    class Meta:
        db_table = 'tb_sku'
        verbose_name = '商品SKU'
        verbose_name_plural = verbose_name

    def __str__(self):
        return '%s: %s' % (self.id, self.name)


class SKUImage(BaseModel):
    """SKU图片"""
    sku_id = models.IntegerField(verbose_name='sku_id')
    image = models.ImageField(verbose_name='图片')

    class Meta:
        db_table = 'tb_sku_image'
        verbose_name = 'SKU图片'
        verbose_name_plural = verbose_name


class SPUSpecification(BaseModel):
    """商品SPU规格"""
    spu_id = models.IntegerField(verbose_name='商品spu_id')
    name = models.CharField(max_length=20, verbose_name='规格名称')

    class Meta:
        db_table = 'tb_spu_specification'
        verbose_name = '商品SPU规格'
        verbose_name_plural = verbose_name


class SpecificationOption(BaseModel):
    """规格选项"""
    spec_id = models.IntegerField(verbose_name='规格id')
    value = models.CharField(max_length=20, verbose_name='选项值')

    class Meta:
        db_table = 'tb_specification_option'
        verbose_name = '规格选项'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.value


class SKUSpecification(BaseModel):
    """SKU具体规格"""
    sku_id = models.IntegerField(verbose_name='sku_id')
    spec_id = models.IntegerField(verbose_name='规格名称id')
    option_id = models.IntegerField(verbose_name='规格值id')

    class Meta:
        db_table = 'tb_sku_specification'
        verbose_name = 'SKU规格'
        verbose_name_plural = verbose_name


class GoodsVisitCount(BaseModel):
    """统计分类商品访问量模型类"""
    category_id = models.IntegerField(verbose_name='商品分类id')
    count = models.IntegerField(verbose_name='访问量', default=0)
    date = models.DateField(auto_now_add=True, verbose_name='统计日期')

    class Meta:
        db_table = 'tb_goods_visit'
        verbose_name = '统计分类商品访问量'
        verbose_name_plural = verbose_name
