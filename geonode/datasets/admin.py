from django.contrib import admin
from geonode.datasets.models import Roda


class RodaAdmin(admin.ModelAdmin):
    model = Roda
    list_display_links = ('requester_username',)
    list_display = ('requester_username', 'requester_name', 'requester_email', 'requester_position', 'requester_institution', 'purposes', 'retention', 'resource_title', 'resource_owner')

    # set permission to view only, not be able to modify the content
    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def save_model(self, request, obj, form, change):
        # Return nothing to make sure user can't update any data
        pass


admin.site.register(Roda, RodaAdmin)
