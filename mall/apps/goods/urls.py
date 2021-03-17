"""mall URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path

from goods import views

app_name = 'goods'
urlpatterns = [
    path('list/<int:category_id>/<int:page_num>/', views.GoodsList, name='goods_list'),
    path('hot/<int:category_id>/', views.GoodsHotList, name='goods_list_hot'),
    path('detail/<int:sku_id>/', views.GoodsDetail, name='goods_detail'),
    path('visit/<int:category_id>/', views.GoodsVisit, name='visit'),

    path('comments/<int:sku_id>/', views.GoodsComments, name='goods_comments')
]
