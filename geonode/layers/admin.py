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

from django.contrib import admin
from django.db.models import Prefetch

from modeltranslation.admin import TabbedTranslationAdmin

from geonode.base.admin import ResourceBaseAdminForm
from geonode.base.admin import metadata_batch_edit, set_batch_permissions
from geonode.layers.models import Layer, Attribute, Style
from geonode.layers.models import LayerFile, UploadSession

from geonode.base.fields import MultiThesauriField
from geonode.base.models import ThesaurusKeyword, ThesaurusKeywordLabel

from dal import autocomplete


class AttributeInline(admin.TabularInline):
    model = Attribute


class LayerAdminForm(ResourceBaseAdminForm):

    class Meta(ResourceBaseAdminForm.Meta):
        model = Layer
        fields = '__all__'

    tkeywords = MultiThesauriField(
        queryset=ThesaurusKeyword.objects.prefetch_related(
            Prefetch('keyword', queryset=ThesaurusKeywordLabel.objects.filter(lang='en'))
        ),
        widget=autocomplete.ModelSelect2Multiple(
            url='thesaurus_autocomplete',
        ),
        label=("Keywords from Thesaurus"),
        required=False,
        help_text=("List of keywords from Thesaurus",),
    )


class LayerAdmin(TabbedTranslationAdmin):
    list_display = (
        'id',
        'alternate',
        'title',
        'date',
        'group',
        'is_approved',
        'is_published',
        'metadata_completeness')
    list_display_links = ('id',)
    list_editable = ('title', 'group', 'is_approved', 'is_published')
    list_filter = ('subtype', 'owner', 'group',
                   'restriction_code_type__identifier', 'date', 'date_type',
                   'is_approved', 'is_published')
    search_fields = ('alternate', 'title', 'abstract', 'purpose',
                     'is_approved', 'is_published',)
    filter_horizontal = ('contacts',)
    date_hierarchy = 'date'
    readonly_fields = ('uuid', 'alternate', 'workspace')
    inlines = [AttributeInline]
    form = LayerAdminForm
    actions = [metadata_batch_edit, set_batch_permissions]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(owner=request.user)

    def has_module_permission(self, request):
        if request.user.is_staff:
            return True

    def has_change_permission(self, request, obj=None):
        if request.user.is_staff:
            return True


class AttributeAdmin(admin.ModelAdmin):
    model = Attribute
    list_display_links = ('id',)
    list_display = (
        'id',
        'layer',
        'attribute',
        'description',
        'attribute_label',
        'attribute_type',
        'display_order')
    list_filter = ('layer', 'attribute_type')
    search_fields = ('attribute', 'attribute_label',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(owner=request.user)

    def has_module_permission(self, request):
        if request.user.is_staff:
            return True

    def has_change_permission(self, request, obj=None):
        if request.user.is_staff:
            return True


class StyleAdmin(admin.ModelAdmin):
    model = Style
    list_display_links = ('sld_title',)
    list_display = ('id', 'name', 'sld_title', 'workspace', 'sld_url')
    list_filter = ('workspace',)
    search_fields = ('name', 'workspace',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(owner=request.user)

    def has_module_permission(self, request):
        if request.user.is_staff:
            return True

    def has_change_permission(self, request, obj=None):
        if request.user.is_staff:
            return True


class LayerFileInline(admin.TabularInline):
    model = LayerFile


class UploadSessionAdmin(admin.ModelAdmin):
    model = UploadSession
    list_display = ('resource', 'date', 'user', 'processed')
    inlines = [LayerFileInline]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(owner=request.user)

    def has_module_permission(self, request):
        if request.user.is_staff:
            return True

    def has_change_permission(self, request, obj=None):
        if request.user.is_staff:
            return True


admin.site.register(Layer, LayerAdmin)
admin.site.register(Attribute, AttributeAdmin)
admin.site.register(Style, StyleAdmin)
admin.site.register(UploadSession, UploadSessionAdmin)
