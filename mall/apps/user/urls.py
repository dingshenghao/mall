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

from user import views

app_name = 'user'
urlpatterns = [
    path('register/', views.Register, name='register'),
    path('image_codes/<uuid>/', views.ImageCode, name='image_code'),
    path('send_codes/<mobile>/', views.SmsCode, name='sms_code'),
    path('usernames/<username>/count/', views.check_username, name='check_username'),
    path('mobiles/<mobile>/count/', views.check_mobile, name='check_mobile'),

    path('login/', views.Login, name='login'),
    path('logout/', views.Logout, name='logout'),

    path('info/', views.UserCenterInfo, name='info'),

    path('emails/', views.SendEmail, name='send_email'),
    path('emails/verify/', views.EmailVerify, name='email_verify'),

    path('password/', views.Password, name='password'),

    path('addresses/', views.Addresses, name='addresses'),
    path('addresses/create/', views.AddressCreate, name='address_create'),
    path('addresses/<int:id>/', views.ChangeAddress, name='change_address'),
    path('addresses/<int:id>/title/', views.ChangeAddressTitle, name='change_address_title'),
    path('addresses/<int:id>/default/', views.ChangeDefaultAddress, name='change_default_address'),

    path('browse_histories/', views.BrowseHistory, name='browse_history'),
]
