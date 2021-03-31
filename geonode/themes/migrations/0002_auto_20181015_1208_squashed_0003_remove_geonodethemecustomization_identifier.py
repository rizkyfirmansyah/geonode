# -*- coding: utf-8 -*-
# Generated by Django 1.11.20 on 2019-04-04 08:34

from django.db import migrations, models


class Migration(migrations.Migration):

    replaces = [('geonode_themes', '0002_auto_20181015_1208'), ('geonode_themes', '0003_remove_geonodethemecustomization_identifier')]

    dependencies = [
        ('geonode_themes', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='geonodethemecustomization',
            name='jumbotron_site_description',
        ),
        migrations.AddField(
            model_name='geonodethemecustomization',
            name='jumbotron_cta_hide',
            field=models.BooleanField(default=False, verbose_name='Hide call to action'),
        ),
        migrations.AddField(
            model_name='geonodethemecustomization',
            name='jumbotron_cta_link',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Call to action link'),
        ),
        migrations.AddField(
            model_name='geonodethemecustomization',
            name='jumbotron_cta_text',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Call to action text'),
        ),
        migrations.AlterField(
            model_name='geonodethemecustomization',
            name='contact_administrative_area',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='geonodethemecustomization',
            name='contact_city',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='geonodethemecustomization',
            name='contact_country',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='geonodethemecustomization',
            name='contact_delivery_point',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='geonodethemecustomization',
            name='contact_email',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='geonodethemecustomization',
            name='contact_name',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='geonodethemecustomization',
            name='contact_position',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='geonodethemecustomization',
            name='contact_postal_code',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='geonodethemecustomization',
            name='contact_street',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='geonodethemecustomization',
            name='contactus',
            field=models.BooleanField(default=False, verbose_name='Enable contact us box'),
        ),
        migrations.AlterField(
            model_name='geonodethemecustomization',
            name='date',
            field=models.DateTimeField(auto_now_add=True, help_text='This will not appear anywhere.'),
        ),
        migrations.AlterField(
            model_name='geonodethemecustomization',
            name='description',
            field=models.TextField(blank=True, help_text='This will not appear anywhere.', null=True),
        ),
        migrations.AlterField(
            model_name='geonodethemecustomization',
            name='is_enabled',
            field=models.BooleanField(default=False, help_text='Enabling this theme will disable the current enabled theme (if any)'),
        ),
        migrations.AlterField(
            model_name='geonodethemecustomization',
            name='jumbotron_bg',
            field=models.ImageField(blank=True, null=True, upload_to='img/%Y/%m', verbose_name='Jumbotron background'),
        ),
        migrations.AlterField(
            model_name='geonodethemecustomization',
            name='jumbotron_welcome_content',
            field=models.TextField(blank=True, null=True, verbose_name='Jumbotron content'),
        ),
        migrations.AlterField(
            model_name='geonodethemecustomization',
            name='jumbotron_welcome_hide',
            field=models.BooleanField(default=False, help_text='Check this if the jumbotron backgroud image already contains text', verbose_name='Hide text in the jumbotron'),
        ),
        migrations.AlterField(
            model_name='geonodethemecustomization',
            name='jumbotron_welcome_title',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Jumbotron title'),
        ),
        migrations.AlterField(
            model_name='geonodethemecustomization',
            name='name',
            field=models.CharField(help_text='This will not appear anywhere.', max_length=100),
        ),
        migrations.AlterField(
            model_name='partner',
            name='href',
            field=models.CharField(max_length=255, verbose_name='Website'),
        ),
        migrations.AlterField(
            model_name='partner',
            name='name',
            field=models.CharField(help_text='This will not appear anywhere.', max_length=100),
        ),
        migrations.AlterField(
            model_name='partner',
            name='title',
            field=models.CharField(max_length=255, verbose_name='Display name'),
        ),
        migrations.RemoveField(
            model_name='geonodethemecustomization',
            name='identifier',
        ),
    ]
