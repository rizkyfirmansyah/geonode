# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2016 OSGeo
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
#########################################################################

from uuid import uuid4
from django import forms
from django.contrib import admin
from django.conf import settings
from django.shortcuts import redirect, render
from django.urls import path
from django.http import HttpResponseRedirect
from dal import autocomplete
from taggit.forms import TagField
from django.core.management import call_command
from slugify import slugify
from django.contrib import messages
from django.utils.translation import ugettext as _

from treebeard.admin import TreeAdmin
from treebeard.forms import movenodeform_factory

from modeltranslation.admin import TabbedTranslationAdmin

from geonode.base.models import (
    TopicCategory,
    DataType,
    SpatialRepresentationType,
    Region,
    RestrictionCodeType,
    ContactRole,
    Link,
    License,
    HierarchicalKeyword,
    MenuPlaceholder,
    Menu,
    MenuItem,
    Configuration,
    Thesaurus, ThesaurusLabel, ThesaurusKeyword, ThesaurusKeywordLabel,
)
from django.core.files.base import ContentFile
from geonode.storage.manager import storage_manager
import random

import csv
from django.db import transaction

from geonode.base.forms import (
    BatchEditForm,
    BatchEditRegionForm,
    BatchPermissionsForm,
    CsvImportForm, ThesaurusImportForm,
    UserAndGroupPermissionsForm
)
from geonode.base.widgets import TaggitSelect2Custom


def metadata_batch_edit(modeladmin, request, queryset):
    ids = ','.join(str(element.pk) for element in queryset)
    resource = queryset[0].class_name.lower()
    form = BatchEditForm({
        'ids': ids
    })
    name_space_mapper = {
        'layer': 'layer_batch_metadata',
        'map': 'map_batch_metadata',
        'dataset': 'dataset_batch_metadata'
    }

    try:
        name_space = name_space_mapper[resource]
    except KeyError:
        name_space = None

    return render(
        request,
        "base/batch_edit.html",
        context={
            'form': form,
            'ids': ids,
            'model': resource,
            'name_space': name_space
        }
    )


metadata_batch_edit.short_description = 'Metadata batch edit'


def set_batch_permissions(modeladmin, request, queryset):
    ids = ','.join(str(element.pk) for element in queryset)
    resource = queryset[0].class_name.lower()
    form = BatchPermissionsForm({
        'ids': ids
    })

    name_space_mapper = {
        'layer': 'layer_batch_permissions',
        'dataset': 'dataset_batch_permissions'
    }

    try:
        name_space = name_space_mapper[resource]
    except KeyError:
        name_space = None

    return render(
        request,
        "base/batch_permissions.html",
        context={
            'form': form,
            'ids': ids,
            'model': resource,
            'name_space': name_space
        }
    )


set_batch_permissions.short_description = 'Set permissions'


def set_user_and_group_layer_permission(modeladmin, request, queryset):
    ids = ','.join(str(element.pk) for element in queryset)
    resource = queryset[0].__class__.__name__.lower()

    model_mapper = {
        "profile": "people",
        "groupprofile": "groups"
    }

    form = UserAndGroupPermissionsForm({
        'permission_type': ('r', ),
        'mode': 'set',
        'ids': ids,
    })

    return render(
        request,
        "base/user_and_group_permissions.html",
        context={
            "form": form,
            "model": model_mapper[resource]
        }
    )


set_user_and_group_layer_permission.short_description = 'Set layer permissions'


class LicenseAdmin(TabbedTranslationAdmin):
    model = License
    list_display = ('id', 'name', 'description')
    list_display_links = ('name',)

    def has_module_permission(self, request):
        if request.user.is_staff:
            return True

    def has_add_permission(self, request):
        if request.user.is_staff:
            return True

    def has_change_permission(self, request, obj=None):
        if request.user.is_staff:
            return True


class TopicCategoryAdmin(TabbedTranslationAdmin):
    model = TopicCategory
    list_display_links = ('identifier',)
    list_display = (
        'identifier',
        'title',
        'gn_description',
        'fa_class',
        'svg',
        'is_choice')
    search_fields = ('title', 'gn_description',)
    if settings.MODIFY_TOPICCATEGORY is False:
        exclude = ('identifier', 'title',)

    def has_add_permission(self, request):
        # the records are from the standard TC 211 list, so no way to add
        if settings.MODIFY_TOPICCATEGORY:
            return True
        else:
            return False

    def has_delete_permission(self, request, obj=None):
        # the records are from the standard TC 211 list, so no way to remove
        if settings.MODIFY_TOPICCATEGORY:
            return True
        else:
            return False

    def has_module_permission(self, request):
        if request.user.is_staff:
            return True

    def has_change_permission(self, request, obj=None):
        if request.user.is_staff:
            return True


class DataTypeAdmin(TabbedTranslationAdmin):
    model = DataType
    list_display_links = ('identifier',)
    list_display = ('identifier', 'title', 'gn_description', 'is_choice')

    def has_add_permission(self, request):
        if request.user.is_staff:
            return True

    def has_delete_permission(self, request, obj=None):
        return True

    def has_module_permission(self, request):
        if request.user.is_staff:
            return True

    def has_change_permission(self, request, obj=None):
        if request.user.is_staff:
            return True


def generate_random_code(string, hash=6):
    code = ''.join(random.choice(string.replace(" ","")) for _ in range(hash)).upper()
    return code


class RegionAdmin(TabbedTranslationAdmin):
    change_list_template = "admin/regions/regions_changelist.html"

    def get_urls(self):
        urls = super().get_urls()
        new_urls = [path('upload_regions/', self.upload_csv),]
        return new_urls + urls

    def upload_csv(self, request):
        toast_title = "Upload Region"
        
        if request.method == "POST":
            csv_file = request.FILES["csv_file"]

            if not csv_file.name.endswith('.csv'):
                msg = f"The wrong file type was uploaded"
                messages.warning(request, msg, extra_tags=toast_title)
                return HttpResponseRedirect(request.path_info)

            upload_path = f"base/regions-{str(uuid4())}.csv"
            content = csv_file.read()
            file_content = ContentFile(content)
            file_name = storage_manager.save(
                upload_path, file_content
            )
            tmp_file = storage_manager.path(file_name)

            csv_file = open(tmp_file, errors="ignore")
            reader = csv.reader(csv_file)

            headers = next(reader, None)

            if len(headers) == 1:
                with transaction.atomic():
                      with Region.objects.delay_mptt_updates():
                          for row in reader:
                              obj = Region(
                                  code=generate_random_code(row[0], hash=6),
                                  name=row[0],
                              )
                              obj.save()

                      Region.objects.rebuild()

            if len(headers) > 1 and "code" not in headers and "parent" in headers:
                with transaction.atomic():
                    with Region.objects.delay_mptt_updates():
                        for row in reader:
                            (
                                name,
                                bbox_x0,
                                bbox_x1,
                                bbox_y0,
                                bbox_y1,
                                parent
                            ) = row
                            parent_id = Region.objects.filter(name__iexact=parent).values_list('id', flat=True)
                            obj = Region(
                                code=generate_random_code(name),
                                name=name,
                                bbox_x0=bbox_x0,
                                bbox_x1=bbox_x1,
                                bbox_y0=bbox_y0,
                                bbox_y1=bbox_y1,
                                parent_id=list(parent_id)[0]
                            )
                            obj.save()

                    Region.objects.rebuild()

            if len(headers) > 1 and "code" not in headers and "parent" not in headers:
                with transaction.atomic():
                    for row in reader:
                        (
                            name,
                            bbox_x0,
                            bbox_x1,
                            bbox_y0,
                            bbox_y1
                        ) = row
                        _code = generate_random_code(name)
                        if Region.objects.filter(code__contains=_code):
                            _code = generate_random_code(name)
                        obj = Region(
                            code=_code,
                            name=name,
                            bbox_x0=bbox_x0,
                            bbox_x1=bbox_x1,
                            bbox_y0=bbox_y0,
                            bbox_y1=bbox_y1
                        )
                        obj.save()

            if len(headers) > 1 and "code" in headers and "parent" in headers:
                with transaction.atomic():
                    with Region.objects.delay_mptt_updates():
                        for row in reader:
                            (
                                name,
                                bbox_x0,
                                bbox_x1,
                                bbox_y0,
                                bbox_y1,
                                parent
                            ) = row
                            parent_id = Region.objects.filter(name__iexact=parent).values_list('id', flat=True)
                            obj = Region(
                                name=name,
                                bbox_x0=bbox_x0,
                                bbox_x1=bbox_x1,
                                bbox_y0=bbox_y0,
                                bbox_y1=bbox_y1,
                                parent_id=list(parent_id)[0]
                            )
                            obj.save()

                    Region.objects.rebuild()

            if len(headers) == 7 and "code" in headers:
                with transaction.atomic():
                    with Region.objects.delay_mptt_updates():
                        for row in reader:
                            (
                                code,
                                name,
                                level,
                                bbox_x0,
                                bbox_x1,
                                bbox_y0,
                                bbox_y1,
                            ) = row
                            obj = Region(
                                code=code,
                                name=name,
                                level=level,
                                bbox_x0=bbox_x0,
                                bbox_x1=bbox_x1,
                                bbox_y0=bbox_y0,
                                bbox_y1=bbox_y1
                            )
                            obj.save()

                    Region.objects.rebuild()

            msg = f"Your region has been imported"
            messages.success(request, msg, extra_tags=toast_title)
            return redirect("..")

        form = CsvImportForm()
        context = {"form": form}

        return render(request, "base/upload_regions.html", context)

    model = Region
    list_display_links = ('name',)
    list_display = ('code', 'name', 'parent')
    search_fields = ('code', 'name',)
    group_fieldsets = True

    def has_module_permission(self, request):
        if request.user.is_staff:
            return True

    def has_change_permission(self, request, obj=None):
        if request.user.is_staff:
            return True


class SpatialRepresentationTypeAdmin(TabbedTranslationAdmin):
    model = SpatialRepresentationType
    list_display_links = ('identifier',)
    list_display = ('identifier', 'title', 'gn_description', 'is_choice')

    def has_add_permission(self, request):
        # the records are from the standard TC 211 list, so no way to add
        return True

    def has_delete_permission(self, request, obj=None):
        # the records are from the standard TC 211 list, so no way to remove
        return True


class RestrictionCodeTypeAdmin(TabbedTranslationAdmin):
    model = RestrictionCodeType
    list_display_links = ('identifier',)
    list_display = ('identifier', 'title', 'gn_description', 'is_choice')

    def has_add_permission(self, request):
        # the records are from the standard TC 211 list, so no way to add
        return True

    def has_delete_permission(self, request, obj=None):
        # the records are from the standard TC 211 list, so no way to remove
        return True

    def has_module_permission(self, request):
        if request.user.is_staff:
            return True

    def has_change_permission(self, request, obj=None):
        if request.user.is_staff:
            return True


class ContactRoleAdmin(admin.ModelAdmin):
    model = ContactRole
    list_display_links = ('id',)
    list_display = ('id', 'contact', 'resource', 'role')
    list_editable = ('contact', 'resource', 'role')
    form = forms.modelform_factory(ContactRole, fields='__all__')


class LinkAdmin(admin.ModelAdmin):
    model = Link
    list_display_links = ('id',)
    list_display = ('id', 'resource', 'extension', 'link_type', 'name', 'mime')
    list_filter = ('resource', 'extension', 'link_type', 'mime')
    search_fields = ('name', 'resource__title',)
    form = forms.modelform_factory(Link, fields='__all__')


class HierarchicalKeywordAdmin(TreeAdmin):
    search_fields = ('name', )
    form = movenodeform_factory(HierarchicalKeyword)


class MenuPlaceholderAdmin(admin.ModelAdmin):
    model = MenuPlaceholder
    list_display = ('name', )


class MenuAdmin(admin.ModelAdmin):
    model = Menu
    list_display = ('title', 'placeholder', 'order')


class MenuItemAdmin(admin.ModelAdmin):
    model = MenuItem
    list_display = ('title', 'menu', 'order', 'blank_target', 'url')


class ConfigurationAdmin(admin.ModelAdmin):
    model = Configuration

    def has_delete_permission(self, request, obj=None):
        # Disable delete action of Singleton model, since "delete selected objects" uses QuerysSet.delete()
        # instead of Model.delete()
        return False

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)

        # allow only superusers to modify Configuration
        if not request.user.is_superuser:
            for field in form.base_fields:
                form.base_fields.get(field).disabled = True

        return form


class ThesaurusAdmin(admin.ModelAdmin):
    change_list_template = "admin/thesauri/change_list.html"

    model = Thesaurus
    list_display = ('id', 'identifier')
    list_display_links = ('id', 'identifier')
    ordering = ('identifier',)

    def get_urls(self):
        urls = super(ThesaurusAdmin, self).get_urls()
        my_urls = [
            path('importrdf/', self.import_rdf, name="base_thesaurus_importrdf")
        ]
        return my_urls + urls

    def import_rdf(self, request):
        if request.method == "POST":
            try:
                rdf_file = request.FILES["rdf_file"]
                name = slugify(rdf_file.name)
                call_command('load_thesaurus', file=rdf_file, name=name)
                self.message_user(request, "Your RDF file has been imported", messages.SUCCESS)
                return redirect("..")
            except Exception as e:
                self.message_user(request, e.args[0], messages.ERROR)
                return redirect("..")

        form = ThesaurusImportForm()
        payload = {"form": form}
        return render(
            request, "admin/thesauri/upload_form.html", payload
        )


class ThesaurusLabelAdmin(admin.ModelAdmin):
    model = ThesaurusLabel
    list_display = ('thesaurus_id', 'lang', 'label')
    list_display_links = ('label',)
    ordering = ('thesaurus__identifier', 'lang')

    def thesaurus_id(self, obj):
        return obj.thesaurus.identifier

    thesaurus_id.short_description = 'Thesaurus'
    thesaurus_id.admin_order_field = 'thesaurus__identifier'


class ThesaurusKeywordAdmin(admin.ModelAdmin):
    model = ThesaurusKeyword

    list_display = ('thesaurus_id', 'about', 'alt_label',)
    list_display_links = ('about', 'alt_label',)
    ordering = ('thesaurus__identifier', 'alt_label',)
    list_filter = ('thesaurus_id',)

    def thesaurus_id(self, obj):
        return obj.thesaurus.identifier

    thesaurus_id.short_description = 'Thesaurus'
    thesaurus_id.admin_order_field = 'thesaurus__identifier'


class ThesaurusKeywordLabelAdmin(admin.ModelAdmin):
    model = ThesaurusKeywordLabel

    list_display = ('thesaurus_id', 'keyword_id', 'lang', 'label')
    list_display_links = ('lang', 'label')
    ordering = ('keyword__thesaurus__identifier', 'keyword__alt_label', 'lang')
    list_filter = ('keyword__thesaurus__identifier', 'keyword_id', 'lang')

    def thesaurus_id(self, obj):
        return obj.keyword.thesaurus.identifier

    thesaurus_id.short_description = 'Thesaurus'
    thesaurus_id.admin_order_field = 'keyword__thesaurus__identifier'

    def keyword_id(self, obj):
        return obj.keyword.alt_label

    keyword_id.short_description = 'Keyword'
    keyword_id.admin_order_field = 'keyword__alt_label'


admin.site.register(TopicCategory, TopicCategoryAdmin)
admin.site.register(DataType, DataTypeAdmin)
admin.site.register(Region, RegionAdmin)
admin.site.register(SpatialRepresentationType, SpatialRepresentationTypeAdmin)
admin.site.register(RestrictionCodeType, RestrictionCodeTypeAdmin)
admin.site.register(ContactRole, ContactRoleAdmin)
admin.site.register(Link, LinkAdmin)
admin.site.register(License, LicenseAdmin)
admin.site.register(HierarchicalKeyword, HierarchicalKeywordAdmin)
admin.site.register(MenuPlaceholder, MenuPlaceholderAdmin)
admin.site.register(Menu, MenuAdmin)
admin.site.register(MenuItem, MenuItemAdmin)
admin.site.register(Configuration, ConfigurationAdmin)
admin.site.register(Thesaurus, ThesaurusAdmin)
admin.site.register(ThesaurusLabel, ThesaurusLabelAdmin)
admin.site.register(ThesaurusKeyword, ThesaurusKeywordAdmin)
admin.site.register(ThesaurusKeywordLabel, ThesaurusKeywordLabelAdmin)


class ResourceBaseAdminForm(autocomplete.FutureModelForm):

    # keywords = TagField(widget=TaggitSelect2Custom('autocomplete_hierachical_keyword'))

    class Meta:
        pass
