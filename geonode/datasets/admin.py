from django.contrib import admin
from geonode.datasets.models import Ropa

class RopaAdmin(admin.ModelAdmin):
    model = Ropa
    list_display_links = ('identifier',)
    list_display = ('identifier', 'requester_name', 'requester_email', 'requester_position', 'requester_institution', 'purposes', 'retention', 'resource_title', 'resource_name', 'resource_owner')

    def has_add_permission(self, request):
        return True

    def has_delete_permission(self, request, obj=None):
        return True

admin.site.register(Ropa, RopaAdmin)