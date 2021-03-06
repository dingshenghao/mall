# Generated by Django 2.2.2 on 2021-02-10 16:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Address',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_time', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('update_time', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('user_id', models.IntegerField(verbose_name='用户')),
                ('title', models.CharField(max_length=20, verbose_name='地址名称')),
                ('receiver', models.CharField(max_length=20, verbose_name='收货人')),
                ('province_id', models.IntegerField(verbose_name='省')),
                ('city_id', models.IntegerField(verbose_name='市')),
                ('district_id', models.IntegerField(verbose_name='区')),
                ('place', models.CharField(max_length=50, verbose_name='地址')),
                ('mobile', models.CharField(max_length=11, verbose_name='手机')),
                ('tel', models.CharField(blank=True, default='', max_length=20, null=True, verbose_name='固定电话')),
                ('email', models.CharField(blank=True, default='', max_length=30, null=True, verbose_name='电子邮箱')),
                ('is_deleted', models.BooleanField(default=False, verbose_name='逻辑删除')),
            ],
            options={
                'verbose_name': '用户地址',
                'verbose_name_plural': '用户地址',
                'db_table': 'address',
                'ordering': ['-update_time'],
            },
        ),
        migrations.AddField(
            model_name='user',
            name='default_address_id',
            field=models.IntegerField(blank=True, null=True, verbose_name='默认地址'),
        ),
    ]
