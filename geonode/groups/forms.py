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

from django import forms
from slugify import slugify
from django.utils.translation import ugettext as _
from modeltranslation.forms import TranslationModelForm
from django.db.models import Q

from django.contrib.auth import get_user_model

from geonode.groups.models import GroupProfile
from django.contrib.auth.models import Group


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

    class Meta:
        model = GroupProfile
        exclude = ['group', 'created_by', ]


class GroupUpdateForm(forms.ModelForm):

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
        exclude = ['group']


class ProfileMultipleChoiceField(forms.ModelMultipleChoiceField):
  
    def label_from_instance(self, obj):
        full_name = ''
        if obj.first_name and obj.last_name and obj.organization:
            full_name = " ".join([obj.first_name, obj.last_name]) + " (" + obj.organization + ")"
            return full_name
        elif obj.first_name and obj.organization:
            full_name = obj.first_name + " (" + obj.organization + ")"
            return full_name
        elif obj.first_name and obj.last_name:
            full_name = " ".join([obj.first_name, obj.last_name])
            return full_name
        elif obj.first_name:
              full_name = obj.first_name
              return full_name
        else:
            return obj.username


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
        required=False,
        label=_("Assign manager role")
    )

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


class GroupsMultipleChoiceField(forms.MultipleChoiceField):
    def label_from_instance(self, obj):
        return obj.title


def get_groups_choices():
    get_groups_choices = [(i.slug, i.name) for i in GroupProfile.objects.all()]
    
    return get_groups_choices


class PermissionsForm(forms.Form):
    get_users = get_user_model().objects.all().exclude(Q(username='AnonymousUser'))

    def __init__(self, *args, **kwargs):
      super().__init__(*args, **kwargs)
      for field in self.fields:
          self.fields[field].widget.attrs.update(
              {
                  'class': 'selectpicker',
                  'data-live-search': 'true',
                  'data-selected-text-format': 'count > 4',
                  'data-actions-box': 'true',
                  'data-size': '5'})

    view_resourcebase_users = ProfileMultipleChoiceField(
      label="The following users",
      queryset=get_users,
      to_field_name="username",
      required=False)
    view_resourcebase_groups = GroupsMultipleChoiceField(
      label="The following groups",
      choices=get_groups_choices,
      required=False)
    download_resourcebase_users = ProfileMultipleChoiceField(
      label="The following users",
      queryset=get_users,
      to_field_name="username",
      required=False)
    download_resourcebase_groups = GroupsMultipleChoiceField(
      label="The following groups",
      choices=get_groups_choices,
      required=False)
    change_resourcebase_metadata_users = ProfileMultipleChoiceField(
      label="The following users",
      queryset=get_users,
      to_field_name="username",
      required=False)
    change_resourcebase_metadata_groups = GroupsMultipleChoiceField(
      label="The following groups",
      choices=get_groups_choices,
      required=False)
    manage_resourcebase_users = ProfileMultipleChoiceField(
      label="The following users",
      queryset=get_users,
      to_field_name="username",
      required=False)
    manage_resourcebase_groups = GroupsMultipleChoiceField(
      label="The following groups",
      choices=get_groups_choices,
      required=False)