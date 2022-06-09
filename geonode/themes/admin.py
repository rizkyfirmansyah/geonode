# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2018 OSGeo
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
#########################################################################

from django import forms
from django.contrib import admin
from .models import Feedback, Partner, GeoNodeThemeCustomization, JumbotronThemeSlide, Faq, About, Help


@admin.register(Partner)
class PartnerAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'title', 'href',)


class GeonodeThemCustomizationForm(forms.ModelForm):
    class Meta:
        model = GeoNodeThemeCustomization
        widgets = {
            'body_color': forms.TextInput(attrs={'type': 'color'}),
            'body_text_color': forms.TextInput(attrs={'type': 'color'}),
            'navbar_color': forms.TextInput(attrs={'type': 'color'}),
            'navbar_text_color': forms.TextInput(attrs={'type': 'color'}),
            'navbar_text_hover': forms.TextInput(attrs={'type': 'color'}),
            'navbar_text_hover_focus': forms.TextInput(attrs={'type': 'color'}),
            'navbar_dropdown_menu': forms.TextInput(attrs={'type': 'color'}),
            'navbar_dropdown_menu_text': forms.TextInput(attrs={'type': 'color'}),
            'navbar_dropdown_menu_hover': forms.TextInput(attrs={'type': 'color'}),
            'navbar_dropdown_menu_divider': forms.TextInput(attrs={'type': 'color'}),
            'jumbotron_color': forms.TextInput(attrs={'type': 'color'}),
            'jumbotron_title_color': forms.TextInput(attrs={'type': 'color'}),
            'jumbotron_text_color': forms.TextInput(attrs={'type': 'color'}),
            'search_bg_color': forms.TextInput(attrs={'type': 'color'}),
            'search_title_color': forms.TextInput(attrs={'type': 'color'}),
            'search_link_color': forms.TextInput(attrs={'type': 'color'}),
            'copyright_color': forms.TextInput(attrs={'type': 'color'}),
            'cookie_law_info_background': forms.TextInput(attrs={'type': 'color'}),
            'cookie_law_info_border': forms.TextInput(attrs={'type': 'color'}),
            'cookie_law_info_button_1_button_colour': forms.TextInput(attrs={'type': 'color'}),
            'cookie_law_info_button_1_button_hover': forms.TextInput(attrs={'type': 'color'}),
            'cookie_law_info_button_1_link_colour': forms.TextInput(attrs={'type': 'color'}),
            'cookie_law_info_button_2_button_colour': forms.TextInput(attrs={'type': 'color'}),
            'cookie_law_info_button_2_button_hover': forms.TextInput(attrs={'type': 'color'}),
            'cookie_law_info_button_2_link_colour': forms.TextInput(attrs={'type': 'color'}),
            'cookie_law_info_button_3_button_colour': forms.TextInput(attrs={'type': 'color'}),
            'cookie_law_info_button_3_button_hover': forms.TextInput(attrs={'type': 'color'}),
            'cookie_law_info_button_3_link_colour': forms.TextInput(attrs={'type': 'color'}),
            'cookie_law_info_button_4_button_colour': forms.TextInput(attrs={'type': 'color'}),
            'cookie_law_info_button_4_button_hover': forms.TextInput(attrs={'type': 'color'}),
            'cookie_law_info_button_4_link_colour': forms.TextInput(attrs={'type': 'color'}),
            'cookie_law_info_showagain_background': forms.TextInput(attrs={'type': 'color'}),
            'cookie_law_info_showagain_border': forms.TextInput(attrs={'type': 'color'}),
            'cookie_law_info_text': forms.TextInput(attrs={'type': 'color'}),
            'footer_bg_color': forms.TextInput(attrs={'type': 'color'}),
            'footer_text_color': forms.TextInput(attrs={'type': 'color'}),
            'footer_href_color': forms.TextInput(attrs={'type': 'color'}),
        }
        fields = '__all__'


@admin.register(GeoNodeThemeCustomization)
class GeoNodeThemeCustomizationAdmin(admin.ModelAdmin):
    form = GeonodeThemCustomizationForm
    list_display = ('id', 'is_enabled', 'name', 'date', 'description')
    list_display_links = ('id', 'name',)


@admin.register(JumbotronThemeSlide)
class JumbotronThemeSlideAdmin(admin.ModelAdmin):
    pass


class FaqFormAdmin(admin.ModelAdmin):
    list_display = ('id', 'header_title', 'contents', 'authenticated_users')
    list_display_links = ('header_title',)
    exclude = ('created_at',)

    def has_module_permission(self, request):
        if request.user.is_staff:
            return True

    def has_add_permission(self, request):
        if request.user.is_staff:
            return True

    def has_change_permission(self, request, obj=None):
        if request.user.is_staff:
            return True


class AboutFormAdmin(admin.ModelAdmin):
    list_display = ('header_title', 'contents')
    list_display_links = ('header_title',)
    exclude = ('created_at',)

    def has_module_permission(self, request):
        if request.user.is_staff:
            return True

    def has_add_permission(self, request):
        if request.user.is_staff:
            return True

    def has_change_permission(self, request, obj=None):
        if request.user.is_staff:
            return True


class HelpFormAdmin(admin.ModelAdmin):
    list_display = ('header_title', 'contents')
    list_display_links = ('header_title',)
    exclude = ('created_at',)

    def has_module_permission(self, request):
        if request.user.is_staff:
            return True

    def has_add_permission(self, request):
        if request.user.is_staff:
            return True

    def has_change_permission(self, request, obj=None):
        if request.user.is_staff:
            return True


class FeedbackFormAdmin(admin.ModelAdmin):
    list_display = ('title', 'details', 'feedback_url', 'feedback_file', 'user', 'created_at')
    list_display_links = ('title',)
    exclude = ('uuid', 'extension', 'feedback_type',)

    def has_module_permission(self, request):
        if request.user.is_staff:
            return True

    def has_view_permission(self, request, obj=None):
        if request.user.is_staff:
            return True


admin.site.register(Faq, FaqFormAdmin)
admin.site.register(About, AboutFormAdmin)
admin.site.register(Help, HelpFormAdmin)
admin.site.register(Feedback, FeedbackFormAdmin)