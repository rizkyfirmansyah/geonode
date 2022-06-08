from django.contrib import admin
from geonode.datasets.models import Roda


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


admin.site.register(Roda, RodaAdmin)
