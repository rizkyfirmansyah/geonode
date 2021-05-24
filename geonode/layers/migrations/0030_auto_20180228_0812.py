# -*- coding: utf-8 -*-
# Generated by Django 1.9.13 on 2018-02-28 14:12

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('services', '0030_auto_20171212_0518'),
        ('layers', '0029_layer_service'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='layer',
            name='service',
        ),
        migrations.AddField(
            model_name='layer',
            name='remote_service',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='services.Service'),
        ),
    ]
