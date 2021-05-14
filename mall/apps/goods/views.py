import datetime
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import render
from django.core.paginator import Paginator, EmptyPage

from mall.utils.response_code import RETCODE
from user.models import User
from .models import GoodsCategory, SKU, SPU, SKUSpecification, SPUSpecification, SpecificationOption, GoodsVisitCount
from contents.utils import get_categories
from .utils import get_breadcrumb
from orders.models import OrderGoods, OrderInfo


def GoodsList(request, category_id, page_num):
    try:
        cat3 = GoodsCategory.objects.get(id=category_id)
    except GoodsCategory.DoesNotExist:
        return HttpResponseForbidden('category_id不存在')
    # 获取查询参数sort
    sort = request.GET.get('sort', 'default')
    if sort == 'price':  # 以价格排序
        sort_field = '-price'
    elif sort == 'hot':
        sort_field = '-sales'
    else:
        sort = 'default'
        sort_field = '-create_time'
    sku_qs = SKU.objects.filter(is_launched=True, category_id=category_id).order_by(sort_field)     # 查询出上架的数据按时间排序
    # 自定义分页器
    paginator = Paginator(sku_qs, 5)
    total_page = paginator.num_pages
    try:
        page_skus = paginator.page(page_num)
    except EmptyPage:
        return HttpResponseForbidden('没有指定页')
    context = {
        'categories': get_categories(),
        'breadcrumb': get_breadcrumb(cat3),
        'category': cat3,
        'page_skus': page_skus,
        'page_num': page_num,
        'total_page': total_page,
        'sort': sort,
    }
    return render(request, 'list.html', context=context)


def GoodsDetail(request, sku_id):
    try:
        sku = SKU.objects.get(id=sku_id)
    except SKU.DoesNotExist:
        return render(request, '404.html')
    try:
        category = GoodsCategory.objects.get(id=sku.category_id)
    except GoodsCategory.DoesNotExist:
        return render(request, '404.html')

    spu = SPU.objects.get(id=sku.spu_id)    # 查询出当前sku对应的spu

    """1.准备当前商品的规格选项列表 [8, 11]"""
    # 获取出当前正显示的sku商品的规格选项id列表
    current_sku_spec_qs = SKUSpecification.objects.filter(sku_id=sku.id).order_by('spec_id')
    current_sku_option_ids = []  # [8, 11]
    for current_sku_spec in current_sku_spec_qs:
        current_sku_option_ids.append(current_sku_spec.option_id)

    """2.构造规格选择仓库
        {(8, 11): 3, (8, 12): 4, (9, 11): 5, (9, 12): 6, (10, 11): 7, (10, 12): 8}
    """
    # 构造规格选择仓库
    temp_sku_qs = SKU.objects.filter(spu_id=spu.id)  # 获取当前spu下的所有sku
    # 选项仓库大字典
    spec_sku_map = {}  # {(8, 11): 3, (8, 12): 4, (9, 11): 5, (9, 12): 6, (10, 11): 7, (10, 12): 8}
    for temp_sku in temp_sku_qs:
        # 查询每一个sku的规格数据
        temp_spec_qs = SKUSpecification.objects.filter(sku_id=temp_sku.id).order_by('spec_id')
        temp_sku_option_ids = []  # 用来包装每个sku的选项值
        for temp_spec in temp_spec_qs:
            temp_sku_option_ids.append(temp_spec.option_id)
        spec_sku_map[tuple(temp_sku_option_ids)] = temp_sku.id

    """3.组合 并找到sku_id 绑定"""
    spu_spec_qs = SPUSpecification.objects.filter(spu_id=spu.id).order_by('id')  # 获取当前spu中的所有规格

    for index, spec in enumerate(spu_spec_qs):  # 遍历当前所有的规格
        spec_option_qs = SpecificationOption.objects.filter(spec_id=spec.id)  # 获取当前规格中的所有选项
        temp_option_ids = current_sku_option_ids[:]  # 复制一个新的当前显示商品的规格选项列表
        for option in spec_option_qs:  # 遍历当前规格下的所有选项
            temp_option_ids[index] = option.id  # [8, 12]
            option.sku_id = spec_sku_map.get(tuple(temp_option_ids))  # 给每个选项对象绑定下他sku_id属性

        spec.spec_options = spec_option_qs  # 把规格下的所有选项绑定到规格对象的spec_options属性上
    context = {
        'categories': get_categories(),
        'breadcrumb': get_breadcrumb(category),
        'sku': sku,  # 当前要显示的sku模型对象
        'category': category,  # 当前的显示sku所属的三级类别
        'spu': spu,  # sku所属的spu
        'spec_qs': spu_spec_qs,  # 当前商品的所有规格数据
    }
    return render(request, 'detail.html', context=context)


def GoodsHotList(request, category_id):
    try:
        cat3 = GoodsCategory.objects.get(id=category_id)
    except GoodsCategory.DoesNotExist:
        return HttpResponseForbidden('category_id不能存在')
    skus = SKU.objects.filter(category_id=category_id).order_by('-sales')[:2]
    hots = []
    for sku in skus:
        hots.append({
            'id': sku.id,
            'default_image_url': sku.default_image.url,
            'name': sku.name,
            'price': sku.price
        })
    return JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'hots': hots})


def GoodsVisit(request, category_id):
    if request.method == 'POST':
        try:
            category = GoodsCategory.objects.get(id=category_id)
        except GoodsCategory.DoesNotExist:
            return HttpResponseForbidden('category_id不存在')

        data = datetime.datetime.now()
        try:
            visit_model = GoodsVisitCount.objects.get(category_id=category_id, date=data)
            visit_model.count += 1
            visit_model.save()
        except GoodsVisitCount.DoesNotExist:
            GoodsVisitCount.objects.create(category_id=category_id, count=1)
    return JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK'})


def GoodsComments(request, sku_id):
    if request.method == 'GET':
        order_goods_models = OrderGoods.objects.filter(sku_id=sku_id, is_commented=True)
        comment_list = []
        for order_goods_model in order_goods_models:
            try:
                order_info = OrderInfo.objects.get(order_id=order_goods_model.order_id)
            except OrderInfo.DoesNotExist:
                return HttpResponseForbidden('商品信息出现错误')
            user_id = order_info.user_id
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return HttpResponseForbidden('用户信息错误')
            # 判断是否时匿名评价
            if order_goods_model.is_anonymous:
                comment = {
                    'name': user.username[0:2] + '*****',
                    'content': order_goods_model.comment,
                    'score': order_goods_model.score
                }
            else:
                comment = {
                    'name': user.username,
                    'content': order_goods_model.comment,
                    'score': order_goods_model.score
                }
            comment_list.append(comment)
        return JsonResponse({"code": RETCODE.OK, 'errmsg': 'OK', 'comment_list': comment_list})