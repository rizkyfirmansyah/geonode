from django import forms
from django.contrib.auth import get_user_model
from geonode.datasets.models import Roda
from geonode.groups.models import GroupProfile
from django.db.models import Q
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext as _

from geonode.people.forms import ProfileMultipleChoiceField


class GroupsMultipleChoiceField(forms.MultipleChoiceField):
    def label_from_instance(self, obj):
        return obj.title


def get_groups_choices():
    get_groups_choices = [(i.slug, i.title) for i in GroupProfile.objects.all()]
    
    return get_groups_choices


def get_groups_id_choices():
    get_groups_choices = [(i.group_id, i.title) for i in GroupProfile.objects.all()]
    
    return get_groups_choices


class PermissionsForm(forms.Form):
    get_users = get_user_model().objects.all().exclude(Q(username='AnonymousUser'))
    if settings.DEFAULT_ANONYMOUS_VIEW_PERMISSION:
        get_users_view = get_user_model().objects.all()
    else:
        get_users_view = get_user_model().objects.all().exclude(Q(username='AnonymousUser'))

    if settings.DEFAULT_ANONYMOUS_DOWNLOAD_PERMISSION:
        get_users_download = get_user_model().objects.all()
    else:
        get_users_download = get_user_model().objects.all().exclude(Q(username='AnonymousUser'))

    def __init__(self, user, *args, **kwargs):
      super().__init__(*args, **kwargs)

      for field in self.fields:
          if 'users' in field or 'groups' in field:
              self.fields[field].widget.attrs.update({
                  'class': 'selectpicker',
                  'data-live-search': 'true',
                  'data-selected-text-format': 'count > 4',
                  'data-actions-box': 'true',
                  'data-size': '5'})
          if 'users' in field:
              self.fields[field].initial = user

    view_resourcebase_users = ProfileMultipleChoiceField(
      label="The following users",
      queryset=get_users_view,
      to_field_name="username",
      required=True)
    view_resourcebase_groups = GroupsMultipleChoiceField(
      label="The following groups",
      choices=get_groups_choices,
      required=False)
    download_resourcebase_users = ProfileMultipleChoiceField(
      label="The following users",
      queryset=get_users_download,
      to_field_name="username",
      required=True)
    download_resourcebase_groups = GroupsMultipleChoiceField(
      label="The following groups",
      choices=get_groups_choices,
      required=False)
    change_resourcebase_metadata_users = ProfileMultipleChoiceField(
      label="The following users",
      queryset=get_users,
      to_field_name="username",
      required=True)
    change_resourcebase_metadata_groups = GroupsMultipleChoiceField(
      label="The following groups",
      choices=get_groups_choices,
      required=False)
    change_layer_data_users = ProfileMultipleChoiceField(
      label="The following users",
      queryset=get_users,
      to_field_name="username",
      required=True)
    change_layer_data_groups = GroupsMultipleChoiceField(
      label="The following groups",
      choices=get_groups_choices,
      required=False)
    change_layer_style_users = ProfileMultipleChoiceField(
      label="The following users",
      queryset=get_users,
      to_field_name="username",
      required=True)
    change_layer_style_groups = GroupsMultipleChoiceField(
      label="The following groups",
      choices=get_groups_choices,
      required=False)
    manage_resourcebase_users = ProfileMultipleChoiceField(
      label="The following users",
      queryset=get_users,
      to_field_name="username",
      required=True)
    manage_resourcebase_groups = GroupsMultipleChoiceField(
      label="The following groups",
      choices=get_groups_choices,
      required=False)

    def clean(self):
        """
        Validate fields that depend on each other
        In this case we need to verify if at least one user or group has
        been selected.
        """
        super().clean()
        view_resourcebase_users = self.cleaned_data.get("view_resourcebase_users")
        download_resourcebase_users = self.cleaned_data.get("download_resourcebase_users")
        if view_resourcebase_users is None and download_resourcebase_users is None:
            # when data in field users/groups is not valid,
            # cleaned_data function will not include the data or its field
            raise ValidationError(_("Must have at least one validated user or group."))
        if not any(view_resourcebase_users) and not any(download_resourcebase_users):
            raise ValidationError(_("Must select at least one user or group."))


class RodaForm(forms.ModelForm):
    """
    Form for record all request resources activity
    """
    requester_name = forms.CharField(label="Name", required=True)
    requester_email = forms.CharField(label="Email", required=True)
    requester_institution = forms.CharField(label="Institution", required=True)
    requester_position = forms.CharField(label="Position", required=True)
    purposes = forms.CharField(label="Purposes", required=True, help_text=Roda.purposes_help_text, widget=forms.Textarea)
    retention = forms.ChoiceField(label="Retention", required=False, help_text=Roda.retention_help_text, choices=Roda.RETENTION_CHOICES)

    class Meta:
        model = Roda
        fields = ["requester_name", "requester_email", "requester_institution",  "requester_position", "purposes", "retention"]
        widgets = {
          'requester_name': forms.TextInput(attrs={'class': 'form-control'}),
          'requester_email': forms.TextInput(attrs={'class': 'form-control'}),
          'requester_institution': forms.TextInput(attrs={'class': 'form-control'}),
          'requester_position': forms.TextInput(attrs={'class': 'form-control'}),
          'purposes': forms.Textarea(attrs={'class': 'form-control', 'placeholder': "Please briefly describe how you intend to use this data?"}),
        }
        exclude = ('created_at', 'absolute_url', 'resource_owner', 'uuid', 'resource_title', 'requester',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['retention'].widget.attrs.update(
            {
                'class': 'selectpicker',
                'data-live-search': 'true',
                'data-size': '5'})
