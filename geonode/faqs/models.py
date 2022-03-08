from django.db import models
from django.utils.translation import ugettext_noop as _
from colorfield.fields import ColorField

# Create your models here.

class GeonodeFaq(models.Model):

  header_title = models.CharField(max_length=255, help_text=_("Title Page"), default="Frequently Asked Questions")
  header_title_color = ColorField(default="#000000")
  contents = models.TextField(null=True, blank=True, help_text=_("Content of the FAQs page"))
  contents_color = ColorField(default="#000000")
  
  class Meta:
      ordering = ("id", )
      verbose_name_plural = 'SDI FAQs'