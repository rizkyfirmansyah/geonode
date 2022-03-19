from django.db import models
from django.utils.translation import ugettext_noop as _
from colorfield.fields import ColorField


class Site(models.Model):

    BOOLEAN_CHOICES = [
      (False, _("False")),
      (True, _("True"))
    ]

    header_title = models.CharField(max_length=255, help_text=_("Title Page"), default="Frequently Asked Questions")
    header_title_color = ColorField(default="#000000", null=True)
    contents = models.TextField(null=True, blank=True, help_text=_("Content of the FAQs page"))
    authenticated_users = models.BooleanField(default=True, verbose_name="Display for authenticated users", choices=BOOLEAN_CHOICES)

    class Meta:
        ordering = ("id", )
        verbose_name_plural = 'SDI FAQs'
