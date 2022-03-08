from django.contrib import admin
from django import forms
from .models import GeonodeFaq

class GeonodeFaqForm(forms.ModelForm):
    class Meta:
        model = GeonodeFaq
        widgets = {
          'contents_color': forms.TextInput(attrs={'type': 'color'})
        }
        fields = '__all__'


@admin.register(GeonodeFaq)
class GeonodeFaqFormAdmin(admin.ModelAdmin):
    form = GeonodeFaqForm
    list_display = ('id', 'header_title', 'contents', 'contents_color')
    list_display_links = ('header_title',)