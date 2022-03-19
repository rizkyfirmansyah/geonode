from django import forms
from .models import Roda


class RodaForm(forms.ModelForm):
    """
    Form for record all request resources activity
    """
    requester_name = forms.CharField(label="Name *", required=True)
    requester_email = forms.CharField(label="Email *", required=True)
    requester_institution = forms.CharField(label="Institution *", required=True)
    requester_position = forms.CharField(label="Position *", required=True)
    purposes = forms.CharField(label="Position *", required=True)
    retention = forms.CharField(label="Retention *", required=False)

    class Meta:
        model = Roda
        fields = ["requester_name", "requester_email", "requester_institution",  "requester_position", "purposes", "retention", "uuid", "resource_title", "requester_username"]
        widgets = {
          'requester_name': forms.TextInput(attrs={'class': 'form-control light-border m-input-space'}),
          'requester_email': forms.TextInput(attrs={'class': 'form-control light-border m-input-space'}),
          'requester_institution': forms.TextInput(attrs={'class': 'form-control light-border m-input-space'}),
          'requester_position': forms.TextInput(attrs={'class': 'form-control light-border m-input-space'}),
          'purposes': forms.TextInput(attrs={'class': 'form-control light-border m-input-space', 'placeholder': "Please briefly describe how you intend to use this data?"}),
          'retention': forms.Select(attrs={'class': 'form-control light-border m-input-space'}, choices=Roda.RETENTION_CHOICES)
        }
