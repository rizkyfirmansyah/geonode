from django import forms
from geonode.datasets.models import Roda

class RodaForm(forms.ModelForm):
    requester_name = forms.CharField(required=True)
    requester_email = forms.CharField(required=True)
    requester_position = forms.CharField(required=True)
    requester_institution = forms.CharField(required=True)
    purposes = forms.CharField(required=True)

    class Meta:
        model = Roda
        fields = ["requester_name", "requester_email", "requester_institution",  "requester_position", "purposes", "retention", "uuid", "resource_title", "requester_username"]