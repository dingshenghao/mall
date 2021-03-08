import os
from alipay import AliPay, AliPayConfig
from django.conf import settings
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, JsonResponse

from orders.models import OrderInfo
from mall.utils.response_code import RETCODE
from .models import Payment

app_private_key_string = open(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), 'keys/app_private_key.pem')).read()
alipay_public_key_string = open(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), 'keys/alipay_public_key.pem')).read()


# 支付宝支付     测试账号  sdvehf9745@sandbox.com   111111    111111
@login_required(login_url='/login/')
def Payments(request, order_id):
    if request.method == 'GET':
        """支付宝支付"""
        user = request.user
        try:
            order = OrderInfo.objects.get(order_id=order_id, user_id=user.id,
                                          status=OrderInfo.ORDER_STATUS_ENUM['UNPAID'])
        except OrderInfo.DoesNotExist:
            return HttpResponseForbidden('order_id有误')
        alipay = AliPay(
            appid=settings.ALIPAY_APPID,
            app_notify_url=None,  # 默认回调url
            app_private_key_string=app_private_key_string,
            # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
            alipay_public_key_string=alipay_public_key_string,
            sign_type="RSA2",  # RSA 或者 RSA2
            debug=settings.ALIPAY_DEBUG,  # 默认False
        )

        # 电脑网站支付，需要跳转到https://openapi.alipay.com/gateway.do? + order_string
        order_string = alipay.api_alipay_trade_page_pay(
            out_trade_no=order_id,  # 订单编号
            total_amount=str(order.total_amount),  # 支付总金额   注意将Decimal转成字符串
            subject='天天商城:%s' % order_id,  # 标题
            return_url=settings.ALIPAY_RETURN_URL,  # 支付成功后重定向的url
            # notify_url="https://example.com/notify"  # 可选, 不填则使用默认notify url
        )
        # 拼接支付宝url
        # 真实环境电脑网站支付网关：https://openapi.alipay.com/gateway.do? + order_string
        # 沙箱环境电脑网站支付网关：https://openapi.alipaydev.com/gateway.do? + order_string
        alipay_url = settings.ALIPAY_URL + '?' + order_string
        response = JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'alipay_url': str(alipay_url)})
        return response


def PaymentStatus(request):
    if request.method == 'GET':
        query_dict = request.GET
        data = query_dict.dict()
        # sign 不能参与签名验证
        sign = data.pop('sign')
        alipay = AliPay(
            appid=settings.ALIPAY_APPID,
            app_notify_url=None,  # 默认回调url
            app_private_key_string=app_private_key_string,
            # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
            alipay_public_key_string=alipay_public_key_string,
            sign_type="RSA2",  # RSA 或者 RSA2
            debug=settings.ALIPAY_DEBUG,  # 默认False
        )
        # 调用它的verify方法进行校验支付结果
        success = alipay.verify(data, sign)
        if success:
            # 获取订单交易号和支付宝交易号
            order_id = data.get('out_trade_no')
            trade_no = data.get('trade_no')
            try:
                # 来保存支付结果前，先查询是否保存过，没保存过再去保存及修改订单状态
                Payment.objects.get(order_id=order_id, trade_id=trade_no)
            except Payment.DoesNotExist:
                Payment.objects.create(
                    order_id=order_id,
                    trade_id=trade_no
                )
                # 修改订单状态
                user = request.user
                OrderInfo.objects.filter(order_id=order_id, user_id=user.id,
                                         status=OrderInfo.ORDER_STATUS_ENUM['UNPAID']).update(
                    status=OrderInfo.ORDER_STATUS_ENUM['UNCOMMENT'])
        else:
            return HttpResponseForbidden('支付失败')
        return render(request, 'pay_success.html', {'trade_id': trade_no})
