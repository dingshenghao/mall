from django.shortcuts import render
from django.core.cache import cache
from django.http import JsonResponse, HttpResponseForbidden

from mall.utils.response_code import RETCODE

from .models import Area


def Areas(request):
    area_id = request.GET.get('area_id')
    # 判断area_id是否存在，如果没有，则为查询所有省的数据
    if area_id is None:
        # 读取缓存中的数据
        province_list = cache.get('province_list')
        if province_list is None:
            provinces = Area.objects.filter(parent_id=None)   # 查询出所有省
            province_list = []
            for province in provinces:
                province_list.append({'id': province.id, 'name': province.name})
            # 将数据存储到缓存中， key    value     timeout
            cache.set('province_list', province_list, 3600 * 24)
        return JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'province_list': province_list})
    else:
        sub_data = cache.get('sub_%s' % area_id)
        if sub_data is None:
            try:
                # 查处对应id的省份
                province = Area.objects.get(id=area_id)
                sub_qs = province.subs.all()
                sub_list = []
                for sub in sub_qs:
                    sub_list.append({'id': sub.id, 'name': sub.name})
                sub_data = {
                    'id': area_id,
                    'name': province.name,
                    'subs': sub_list
                }
                cache.set('sub_%s' % area_id, sub_data, 3600 * 24)
            except Area.DoesNotExist:
                return HttpResponseForbidden('area_id不存在')
        return JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'sub_data': sub_data})