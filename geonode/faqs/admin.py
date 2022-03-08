from django.contrib import admin
from django import forms
from .models import GeonodeFaq

class GeonodeFaqForm(forms.ModelForm):
    class Meta:
        model = GeonodeFaq
        fields = '__all__'


@admin.register(GeonodeFaq)
class GeonodeFaqFormAdmin(admin.ModelAdmin):
    form = GeonodeFaqForm
    list_display = ('id', 'header_title', 'contents', 'authenticated_users')
    list_display_links = ('header_title',)