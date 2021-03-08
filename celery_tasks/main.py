# -*- encode: utf-8 -*-
# @Author: dsh
# Time: 2021/2/9 下午2:48

from celery import Celery
import os

# 让celery在启动时提前加载django配置文件， 使用这个的时候就可以导入celery_tasks以外的包
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mall.settings.dev')

# 创建celery客户端对象
celery_app = Celery()

# 加载celery配置，指定celery生产的任务放到哪里
celery_app.config_from_object('celery_tasks.config')

# 注册celery可以生产什么任务
celery_app.autodiscover_tasks(['celery_tasks.sms', 'celery_tasks.email'])