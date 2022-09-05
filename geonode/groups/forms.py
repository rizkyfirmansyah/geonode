# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2017 OSGeo
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

from secrets import choice
from django import forms
from slugify import slugify
from django.utils.translation import ugettext as _
from geonode.security.forms import ProfileMultipleChoiceField
from modeltranslation.forms import TranslationModelForm
from django.db.models import Q
from django.contrib.auth import get_user_model

from geonode.groups.models import GroupProfile


class GroupForm(TranslationModelForm):

    slug = forms.SlugField(
        help_text=_("a short version of the name consisting only of letters, numbers, underscores and hyphens."),
        widget=forms.HiddenInput,
        required=False)

    def clean_slug(self):
        if GroupProfile.objects.filter(
                slug__iexact=self.cleaned_data["slug"]).count() > 0:
            raise forms.ValidationError(
                _("A group already exists with that slug."))
        return self.cleaned_data["slug"].lower()

    def clean_title(self):
        if GroupProfile.objects.filter(
                title__iexact=self.cleaned_data["title"]).count() > 0:
            raise forms.ValidationError(
                _("A group already exists with that name."))
        return self.cleaned_data["title"]

    def clean(self):
        cleaned_data = self.cleaned_data

        name = cleaned_data.get("title")
        slug = slugify(name)

        cleaned_data["slug"] = slug

        return cleaned_data

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.fields["categories"].label = 'Group Categories'
        self.fields["categories"].widget.attrs.update(
              {
                  'class': 'selectpicker',
                  'data-live-search': 'true',
                  'data-selected-text-format': 'count > 4',
                  'data-actions-box': 'true',
                  'data-size': '5'})

    class Meta:
        model = GroupProfile
        exclude = ['group', 'created_by', ]


class GroupUpdateForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["categories"].widget.attrs.update(
              {
                  'class': 'selectpicker',
                  'data-live-search': 'true',
                  'data-selected-text-format': 'count > 4',
                  'data-actions-box': 'true',
                  'data-size': '5'})

    def clean_name(self):
        if GroupProfile.objects.filter(
                name__iexact=self.cleaned_data["title"]).count() > 0:
            if self.cleaned_data["title"] == self.instance.name:
                pass  # same instance
            else:
                raise forms.ValidationError(
                    _("A group already exists with that name."))
        return self.cleaned_data["title"]

    class Meta:
        model = GroupProfile
        exclude = ['group', 'title_en', 'description_en', 'created_by']


class GroupMemberForm(forms.Form):
    get_users = get_user_model().objects.all().exclude(Q(username='AnonymousUser'))

    user_identifiers = ProfileMultipleChoiceField(
        label='Registered Users',
        queryset=get_users,
        widget=forms.SelectMultiple(
            attrs={
                'class': 'selectpicker',
                'data-live-search': 'true',
                'data-selected-text-format': 'count > 4',
                'data-actions-box': 'true',
                'data-size': '5'
        }),
        required=False)

    manager_role = forms.BooleanField(
        required=False
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        manager_role_choices=(
            (True, "Assign manager role"),
            (False, "Assign to member"))

        self.fields['manager_role'].widget.attrs.update({
            'data-toggle': 'toggle',
            'data-width': '100%',
            'data-height': 'auto',
            'data-on': manager_role_choices[0][1],
            'data-off': manager_role_choices[1][1],
            'value': manager_role_choices[0][0],
            'data-onstyle': 'info',
            'data-offstyle': 'primary'})
        self.fields['manager_role'].label = ''


    def clean_user_identifiers(self):
        values = list(self.cleaned_data['user_identifiers'])
        new_members = []
        errors = []
        for name in values:
            try:
                new_members.append(get_user_model().objects.get(username=name))
            except get_user_model().DoesNotExist:
                errors.append(name)
        if errors:
            raise forms.ValidationError(
                _("The following are not valid usernames: %(errors)s; "
                  "not added to the group"),
                params={
                    "errors": ", ".join(errors)
                }
            )
        return new_members