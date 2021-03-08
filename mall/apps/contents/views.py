from django.shortcuts import render

from contents.models import Content, ContentCategory
from .utils import get_categories


def Index(request):
    contents = {}
    category_list = ContentCategory.objects.all()    # 查询出所有广告哦类别
    for category in category_list:
        # 查询出需要展示的广告，按sequence排序，赋值给contents
        contents[category.key] = Content.objects.filter(status=True, category_id=category.id).order_by('sequence')
    context = {
        'categories': get_categories(),
        'contents': contents,
    }
    return render(request, 'index.html', context=context)
