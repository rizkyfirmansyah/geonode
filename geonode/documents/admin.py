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

from modeltranslation.admin import TabbedTranslationAdmin

from geonode.documents.models import Document
from geonode.base.admin import ResourceBaseAdminForm
from geonode.base.admin import metadata_batch_edit


class DocumentAdminForm(ResourceBaseAdminForm):
    class Meta(ResourceBaseAdminForm.Meta):
        model = Document
        fields = '__all__'
        # exclude = (
        #     'resource',
        # )


class DocumentAdmin(TabbedTranslationAdmin):
    list_display = ('id',
                    'title',
                    'date',
                    'group',
                    'is_approved',
                    'is_published',
                    'metadata_completeness')
    list_display_links = ('id',)
    list_editable = ('title', 'group', 'is_approved', 'is_published')
    list_filter = ('date', 'date_type', 'restriction_code_type',
                   'group', 'is_approved', 'is_published',)
    search_fields = ('title', 'abstract', 'purpose',
                     'is_approved', 'is_published',)
    date_hierarchy = 'date'
    form = DocumentAdminForm
    actions = [metadata_batch_edit]

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


admin.site.register(Document, DocumentAdmin)
