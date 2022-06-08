from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _


class Roda(models.Model):
    """
    Table for record of datasets activities
    When users request to download and use of classified data, this table holds information needed to record all requests
    """
    RETENTION_CHOICES = [
      ("one_day", _("1 day")),
      ("one_week", _("1 week")),
      ("one_month", _("1 month")),
      ("six_months", _("6 months")),
      ("one_year", _("1 year")),
      ("two_years", _("2 years")),
      ("three_years", _("3 years")),
      ("five_years", _("5 years")),
      ("forever", _("Forever")),
    ]

    purposes_help_text = _("Please briefly describe how you intend to use this Dataset.")
    retention_help_text = _("Duration the data should be used, stored, or achived.")
    requester_help_text = _("Requester Name")
    resource_owner_help_text = _("Resource Owner")

    uuid = models.CharField(max_length=255)
    requester_name = models.CharField(max_length=255)
    requester_email = models.CharField(max_length=255, null=True, blank=True)
    requester_institution = models.CharField(max_length=255)
    requester_position = models.CharField(max_length=255)
    purposes = models.TextField(default='', help_text=purposes_help_text)
    retention = models.CharField(
        _('Retention'),
        max_length=255,
        choices=RETENTION_CHOICES,
        null=True,
        blank=True,
        help_text=retention_help_text)
    resource_title = models.CharField(max_length=255)
    requester = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, help_text=requester_help_text, related_name='requester')
    resource_owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, help_text=resource_owner_help_text, related_name='resource_owner')
    absolute_url = models.CharField(max_length=255)
    created_at = models.DateTimeField(_('Created Date'), auto_now_add=True, blank=True, null=True)

    class Meta:
        ordering = ["id"]
        verbose_name_plural = "Record of Datasets Activities"


    def __str__(self):
        return str(self.requester)
