# Generated by Django 2.2.16 on 2021-02-23 12:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0053_auto_20210223_0905'),
    ]

    operations = [
        migrations.AlterField(
            model_name='thesaurus',
            name='id',
            field=models.AutoField(primary_key=True, serialize=False, unique=True),
        ),
    ]
