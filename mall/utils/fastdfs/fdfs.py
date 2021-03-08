# -*- encoding:UTF-8 -*-
# @Author: dsh
# Time: 2021/1/22 下午4:50

from fdfs_client.client import Fdfs_client


client = Fdfs_client('/home/ding/PycharmProjects/mall/mall/utils/fastdfs/client.conf')
ret = client.upload_by_filename('/home/ding/PycharmProjects/mall/2.jpg')

print(ret)

# getting connection
# <fdfs_client.connection.Connection object at 0x7f6a9c1cacd0>
# <fdfs_client.fdfs_protol.Tracker_header object at 0x7f6a9c1cac70>
# {'Group name': 'group1',
# 'Remote file_id': 'group1/M00/00/02/wKhJgGAklEmALzAIAAK0I2FpG4g993.jpg',
# 'Status': 'Upload successed.',
# 'Local file name': '/home/ding/PycharmProjects/mall/preview.jpg',
# 'Uploaded size': '173.00KB', 'Storage IP': '192.168.73.128'}