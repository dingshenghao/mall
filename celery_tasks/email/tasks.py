# -*- encode: utf-8 -*-
# @Author: dsh
# Time: 2021/2/10 下午12:25
from django.core.mail import send_mail
from mall.settings.dev import EMAIL_FROM
from celery_tasks.main import celery_app


@celery_app.task()
def send_email(to_email, verify_url):
    """
    发送邮箱激活链接
    :param to_email: 收件邮箱
    :param verify_url: 激活链接
    :return:
    """
    subject = '天天商城邮箱激活'
    html_message = '<p>尊敬的用户您好！</p>' \
                   '<p>感谢您使用天天商城。</p>' \
                   '<p>您的邮箱为：%s 。请点击此链接激活您的邮箱：</p>' \
                   '<p><a href="%s">%s</a></p>' % (to_email, verify_url, verify_url)
    send_mail(subject, '', EMAIL_FROM, [to_email], html_message=html_message)