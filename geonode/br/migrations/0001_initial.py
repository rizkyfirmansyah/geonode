# Generated by Django 2.2.16 on 2021-05-24 21:19

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='RestoredBackup',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=400)),
                ('archive_md5', models.CharField(max_length=32)),
                ('restoration_date', models.DateTimeField(default=datetime.datetime.now)),
                ('creation_date', models.DateTimeField()),
            ],
        ),
    ]
