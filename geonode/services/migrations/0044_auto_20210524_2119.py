# Generated by Django 2.2.16 on 2021-05-24 21:19

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('services', '0043_auto_20210519_1308'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='service',
            name='description_en',
        ),
        migrations.RemoveField(
            model_name='service',
            name='name_en',
        ),
    ]
