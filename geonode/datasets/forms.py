from django import forms
from geonode.datasets.models import Ropa

class RopaForm(forms.ModelForm):

    requester_name = forms.CharField(required=True)
    requester_email = forms.CharField(required=True)
    requester_position = forms.CharField(required=True)
    requester_institution = forms.CharField(required=True)
    purposes = forms.CharField(required=True)
    retention = forms.CharField(required=False)
    # resourcebase_ptr_id = forms.IntegerField(required=False)
    # resource_title = forms.CharField(required=False)
    # resource_name = forms.CharField(required=False)
    # resource_owner = forms.CharField(required=False)
    
    class Meta:
        model = Ropa
        fields = ("requester_name", "requester_email", "requester_position", "requester_institution", "purposes", "retention")