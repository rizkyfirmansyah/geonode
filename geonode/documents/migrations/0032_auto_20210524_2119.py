# Generated by Django 2.2.16 on 2021-05-24 21:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('documents', '0031_auto_20201107_2241'),
    ]

    operations = [
        migrations.AlterField(
            model_name='document',
            name='constraints_other_en',
            field=models.TextField(blank=True, help_text='other restrictions and legal prerequisites for accessing and using the resource or metadata', null=True, verbose_name='Restrictions other'),
        ),
        migrations.AlterField(
            model_name='document',
            name='data_quality_statement_en',
            field=models.TextField(blank=True, help_text="general explanation of the data producer's knowledge about the lineage of a dataset", max_length=2000, null=True, verbose_name='Data quality statement'),
        ),
        migrations.AlterField(
            model_name='document',
            name='supplemental_information_en',
            field=models.TextField(default='No information provided', help_text='any other descriptive information about the dataset', max_length=2000, null=True, verbose_name='Supplemental information'),
        ),
    ]
