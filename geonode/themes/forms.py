from django import forms
from .models import Feedback
from django.utils.translation import ugettext as _


class FeedbackForm(forms.ModelForm):
    title = forms.CharField(
        label=_("How can we improve?"),
        required=True)
    details = forms.CharField(
        required=True,
        widget=forms.Textarea)
    feedback_url = forms.CharField(
        required=False)
    feedback_file = forms.FileField(
        help_text=Feedback.feedback_file_help_text,
        required=False)

    class Meta:
        model = Feedback
        fields = ("title", "details", "feedback_url", "feedback_file",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['details'].widget.attrs['rows'] = 10
        self.fields['details'].widget.attrs['columns'] = 15
        self.fields['details'].widget.attrs.update({'class' : ''})
        self.fields['feedback_file'].label = ''
        self.fields['details'].widget.attrs['placeholder'] = Feedback.details_help_text
        self.fields['details'].widget.attrs['feedback_url'] = Feedback.feedback_url_help_text