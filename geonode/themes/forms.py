from django import forms
from .models import Feedback


class FeedbackForm(forms.ModelForm):
    title = forms.CharField(
        required=True)
    details = forms.CharField(
        required=True,
        widget=forms.Textarea)
    feedback_url = forms.CharField(
        required=False)
    feedback_file = forms.FileField()

    class Meta:
        model = Feedback
        fields = ("title", "details", "feedback_url", "feedback_file",)
