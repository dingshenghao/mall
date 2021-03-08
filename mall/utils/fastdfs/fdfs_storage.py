# -*- encoding:UTF-8 -*-
# @Author: dsh
# Time: 2021/1/22 下午8:18

from django.core.files.storage import Storage
from fdfs_client.client import Fdfs_client
from django.conf import settings


class FdfsStorage(Storage):
    """自定义文件存储类"""

    def __init__(self, client_path=None, base_url=None):
        self.client_path = client_path or settings.FDFS_CLIENT_CONF   # FastDFS客户端配置路径
        self.base_url = base_url or settings.FDFS_URL   # storage服务器的ip和端口

    def _open(self, name, mode='rb'):
        """
        用来打开文件，但是我们自定义文件存储系统是为了实现FastDFS服务，不需要打开文件，所以此方法重写后什么都不做
        :param name: 要打开的文件名
        :param mode: 打开文件的方式 read bytes
        :return: None
        """
        pass

    def _save(self, name, content):
        """
        文件存储的时候调用此方法，但是默认是存储到本地的，需要重写，上传到FastDFS服务器上
        :param name: 要上传的文件名
        :param content: 以rb模式打开的文件对象，将来通过content.read(),就可以读取到文件的二进制数据
        :return: file_id
        """
        # 创建FastDFS客户端
        client = Fdfs_client(self.client_path)
        # 通过客户端调用上传文件的方法上传文件到FastDFS服务器
        # client.upload_by_filename('要上传的文件的绝对路径')   只能通过文件的绝对路径上传，上传的文件有后缀
        # upload_by_buffer可以通过文件二进制数据上传，，上传的文件没有后缀
        ret = client.upload_by_buffer(content.read())
        # 判断文件是否上传成功
        if ret.get('Status') != 'Upload successed.':
            raise Exception('Upload file failed')
        # 获取file_id
        file_id = ret.get('Remote file_id')
        # 返回file_id
        return file_id

    def exists(self, name):
        """
        当要进行文件上传时调用此方法判断文件是否已上传，如果没有上传才会调用save()方法进行上传
        :param name:要上传的文件名
        :return:True(表示文件已存在，不需要上传)，False(文件不存在，需要上传)
        """
        return False

    def url(self, name):
        """
        当要访问图片时，就会调用此方法，获取图片文件的绝对路径
        :param name:要访问图片的file_id
        :return:完整的图片访问路径 http://192.168.73.128:8888/
        """
        # return 'http://192.168.73.128:8888/' + name
        # return settings.FDFS_URL + name
        return self.base_url + name