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
      ("three_year", _("3 years")),
      ("five_year", _("5 years")),
      ("forever", _("Forever")),
    ]

    retention_help_text = _("Duration the data should be used, stored, or achived.")

    uuid = models.CharField(max_length=255)
    requester_username = models.CharField(max_length=150)
    requester_name = models.CharField(max_length=255)
    requester_email = models.CharField(max_length=255)
    requester_position = models.CharField(max_length=255)
    requester_institution = models.CharField(max_length=255)
    purposes = models.TextField(default='')
    retention = models.CharField(
      _('Retention'),
      max_length=255, 
      choices=RETENTION_CHOICES,
      help_text=retention_help_text)
    resource_title = models.CharField(max_length=255)
    resource_owner = models.CharField(max_length=255)

    def __str__(self):
        return self.resource_title

    class Meta:
        ordering = ["id"]
        verbose_name_plural = "Record of Datasets Activities"