from django.contrib import admin
from django import forms
from .models import Site


class SiteForm(forms.ModelForm):
    class Meta:
        model = Site
        fields = '__all__'


@admin.register(Site)
class SiteFormAdmin(admin.ModelAdmin):
    form = SiteForm
    list_display = ('id', 'header_title', 'contents', 'authenticated_users')
    list_display_links = ('header_title',)
