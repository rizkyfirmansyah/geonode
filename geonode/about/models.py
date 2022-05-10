from django.db import models
from django.utils.translation import ugettext_noop as _
from django.utils.timezone import now

class About(models.Model):

    title = models.CharField(_('title'), null=True, blank=True, max_length=255)
    contents = models.TextField(null=True, blank=True, help_text=_("Content of the About page"))
    created_date = models.DateTimeField(_('date'), default=now)

    class Meta:
        ordering = ("id", )
        verbose_name_plural = 'SDI About Site'

class Help(models.Model):

    title = models.CharField(_('title'), null=True, blank=True, max_length=255)
    contents = models.TextField(null=True, blank=True, help_text=_("Content of the Help & Support page"))
    created_date = models.DateTimeField(_('date'), default=now)

    class Meta:
        ordering = ("id", )
        verbose_name_plural = 'SDI Help & Support Site'