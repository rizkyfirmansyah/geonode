from django.contrib import admin
from .models import Faq, About, Help


class FaqFormAdmin(admin.ModelAdmin):
    list_display = ('id', 'header_title', 'contents', 'authenticated_users')
    list_display_links = ('header_title',)
    exclude = ('created_date',)

class AboutFormAdmin(admin.ModelAdmin):
    list_display = ('header_title', 'contents')
    list_display_links = ('header_title',)
    exclude = ('created_date',)


class HelpFormAdmin(admin.ModelAdmin):
    list_display = ('header_title', 'contents')
    list_display_links = ('header_title',)
    exclude = ('created_date',)


admin.site.register(Faq, FaqFormAdmin)
admin.site.register(About, AboutFormAdmin)
admin.site.register(Help, HelpFormAdmin)