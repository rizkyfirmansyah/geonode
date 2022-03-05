from django.contrib import admin
from geonode.datasets.models import Ropa

class RopaAdmin(admin.ModelAdmin):
    model = Ropa
    list_display_links = ('uuid',)
    list_display = ('uuid', 'requester_name', 'requester_email', 'requester_position', 'requester_institution', 'purposes', 'retention', 'resource_title', 'resource_owner_id', 'resource_owner')

    def has_add_permission(self, request):
        return True

    def has_delete_permission(self, request, obj=None):
        return True

admin.site.register(Ropa, RopaAdmin)