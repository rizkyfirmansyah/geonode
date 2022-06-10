from django import forms
from django.contrib.auth import get_user_model
from geonode.groups.models import GroupProfile
from django.db.models import Q


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


class GroupsMultipleChoiceField(forms.MultipleChoiceField):
    def label_from_instance(self, obj):
        return obj.title


class PermissionsForm(forms.Form):
    get_users = get_user_model().objects.all().exclude(Q(username='AnonymousUser'))
    if GroupProfile.objects.all().exists():
        get_groups_choices = [(i.slug, i.title) for i in GroupProfile.objects.all()]
    else:
        get_groups_choices = [""]

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