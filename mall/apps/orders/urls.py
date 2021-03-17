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

from orders import views

app_name = 'orders'
urlpatterns = [
        path('orders/settlement/', views.OrdersSettlement, name='orders_settlement'),   # 订单结算
        path('orders/commit/', views.OrdersCommit, name='order_commit'),    # 提交订单
        path('orders/success/', views.OrdersSuccess, name='orders_success'),
        path('orders/info/1/', views.Order_Info, name='order_info'),

        path('orders/comment/', views.GoodsComment, name='goods_comment'),
]
