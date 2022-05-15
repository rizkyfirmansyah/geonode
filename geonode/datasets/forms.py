from django import forms
from .models import Roda


class RodaForm(forms.ModelForm):
    """
    Form for record all request resources activity
    """
    requester_name = forms.CharField(label="Name", required=True)
    requester_email = forms.CharField(label="Email", required=True)
    requester_institution = forms.CharField(label="Institution", required=True)
    requester_position = forms.CharField(label="Position", required=True)
    purposes = forms.CharField(label="Purposes", required=True, help_text=Roda.purposes_help_text)
    retention = forms.ChoiceField(label="Retention", required=False, help_text=Roda.retention_help_text, choices=Roda.RETENTION_CHOICES)

    class Meta:
        model = Roda
        fields = ["requester_name", "requester_email", "requester_institution",  "requester_position", "purposes", "retention"]
        widgets = {
          'requester_name': forms.TextInput(attrs={'class': 'form-control'}),
          'requester_email': forms.TextInput(attrs={'class': 'form-control'}),
          'requester_institution': forms.TextInput(attrs={'class': 'form-control'}),
          'requester_position': forms.TextInput(attrs={'class': 'form-control'}),
          'purposes': forms.TextInput(attrs={'class': 'form-control', 'placeholder': "Please briefly describe how you intend to use this data?"}),
        }
        exclude = ('created_at', 'absolute_url', 'resource_owner', 'uuid', 'resource_title', 'requester',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['retention'].widget.attrs.update(
            {
                'class': 'selectpicker',
                'data-live-search': 'true',
                'data-size': '5'})
