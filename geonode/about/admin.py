from django.contrib import admin
from django import forms
from .models import About, Help


class AboutForm(forms.ModelForm):
    class Meta:
        model = About
        exclude = ('created_date',)


class HelpForm(forms.ModelForm):
    class Meta:
        model = Help
        exclude = ('created_date',)


@admin.register(About)
class AboutFormAdmin(admin.ModelAdmin):
    form = AboutForm
    list_display = ('title', 'contents')
    list_display_links = ('title',)


@admin.register(Help)
class HelpFormAdmin(admin.ModelAdmin):
    form = HelpForm
    list_display = ('title', 'contents')
    list_display_links = ('title',)