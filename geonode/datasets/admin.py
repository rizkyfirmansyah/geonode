from django.contrib import admin
from ..base.models import ResourceBase
from geonode.datasets.models import Dataset, Roda, File
from geonode.base.admin import ResourceBaseAdminForm
from geonode.base.admin import metadata_batch_edit, set_batch_permissions
from modeltranslation.admin import TabbedTranslationAdmin


class RodaAdmin(admin.ModelAdmin):
    model = Roda
    list_display_links = ('requester',)
    list_display = ('requester', 'requester_name', 'requester_email',
                    'requester_position', 'requester_institution', 'purposes', 'retention',
                    'resource_title', 'resource_owner', 'absolute_url', 'created_at')

    # set permission to view only, not be able to modify the content
    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return True

    def save_model(self, request, obj, form, change):
        # Return nothing to make sure user can't update any data
        pass

    def has_module_permission(self, request):
        if request.user.is_staff:
            return True

    def has_view_permission(self, request, obj=None):
        if request.user.is_staff:
            return True


class DatasetAdminForm(ResourceBaseAdminForm):
    class Meta(ResourceBaseAdminForm.Meta):
        model = Dataset
        fields = '__all__'

class FileInline(admin.TabularInline):
    model = File
    fields = ['file_name', 'file_description', 'file_data_quality', 'file_url',]


class DatasetAdmin(TabbedTranslationAdmin):
    list_display = ('id',
                    'title',
                    'date',
                    'group',
                    'is_approved',
                    'is_published',
                    'metadata_completeness')
    list_editable = ('title', 'group', 'is_approved', 'is_published')
    list_filter = ('date', 'date_type', 'restriction_code_type',
                   'group', 'is_approved', 'is_published',)
    search_fields = ('title', 'abstract', 'purpose',
                     'is_approved', 'is_published',)
    date_hierarchy = 'date'
    inlines = [FileInline,]
    exclude = ('bbox_polygon', 'll_bbox_polygon', 'csw_typename', 'csw_schema', 'csw_mdsource', 'csw_insert_date', 'csw_type',
              'metadata_xml', 'temporal_extent_start', 'temporal_extent_end',
              'spatial_resolution', 'spatial_representation_type', 'srid', 'state', 'source_type', 'remote_typename', 'hash', 'file_size', 'files', 'blob', 'sourcetype', 'csw_anytext', 'csw_wkt_geometry', 'subtype',)
    form = DatasetAdminForm
    actions = [metadata_batch_edit, set_batch_permissions]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(owner=request.user, resource_type='dataset')

    def delete_queryset(self, request, queryset):
        """
        We need to invoke the 'ResourceBase.delete' method even when deleting
        through the admin batch action
        """
        for obj in queryset:
            from geonode.resource.manager import resource_manager
            resource_manager.delete(obj.uuid, instance=obj)

    def has_module_permission(self, request):
        if request.user.is_staff:
            return True

    def has_change_permission(self, request, obj=None):
        if request.user.is_staff:
            return True


admin.site.register(Dataset, DatasetAdmin)
admin.site.register(Roda, RodaAdmin)