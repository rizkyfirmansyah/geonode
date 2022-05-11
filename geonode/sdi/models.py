import logging
import os
from django.db.models import signals
import uuid
from django.db import models
from django.utils.translation import ugettext_noop as _
from colorfield.fields import ColorField
from django.utils.timezone import now
from geonode.documents.enumerations import DOCUMENT_TYPE_MAP
from geonode.sdi.utils import get_unique_feedback_path
from uuid_upload_path import upload_to
from django.conf import settings
from django.contrib.staticfiles import finders
from django.core.files.base import ContentFile
from geonode.storage.manager import storage_manager

logger = logging.getLogger(__name__)

class Faq(models.Model):

    AUTHENTICATED_CHOICES = [
      (False, _("For anyone including not a registered user")),
      (True, _("Certainly yes!"))
    ]

    header_title = models.CharField(max_length=255, verbose_name=_("Title Page"), default="Frequently Asked Questions", null=True, blank=True)
    header_title_color = ColorField(default="#000000", verbose_name=_("Set the text color of the title"), null=True, blank=True)
    contents = models.TextField(verbose_name=_("Content of the FAQs page"), null=True, blank=True)
    authenticated_users = models.BooleanField(default=True, verbose_name=_("Display for registered users?"), choices=AUTHENTICATED_CHOICES)
    created_date = models.DateTimeField(_('Created Date'), default=now)

    def __str__(self) -> str:
        return super().__str__(self.header_title)

    class Meta:
        ordering = ("id", )
        verbose_name_plural = 'SDI FAQs'


class About(models.Model):

    header_title = models.CharField(max_length=255, verbose_name=_("Title Page"), default=_("About SDI"), null=True, blank=True)
    header_title_color = ColorField(default="#000000", verbose_name=_("Set the text color of the title"), null=True, blank=True)
    contents = models.TextField(verbose_name=_("Content of the About page"), null=True, blank=True)
    created_date = models.DateTimeField(_('Created Date'), default=now)

    def __str__(self) -> str:
        return super().__str__(self.header_title)

    class Meta:
        ordering = ("id", )
        verbose_name_plural = 'SDI About'


class Help(models.Model):

    header_title = models.CharField(max_length=255, verbose_name=_("Title Page"), default=_("Help & Support"), null=True, blank=True)
    header_title_color = ColorField(default="#000000", verbose_name=_("Set the text color of the title"), null=True, blank=True)
    contents = models.TextField(verbose_name=_("Content of the Help & Support page"), null=True, blank=True)
    created_date = models.DateTimeField(_('Created Date'), default=now)

    def __str__(self) -> str:
        return super().__str__(self.header_title)

    class Meta:
        ordering = ("id", )
        verbose_name_plural = 'SDI Help & Support'


class Feedback(models.Model):
    feedback_file_help_text = _("add a Screenshot or Video (recommended)")
    details_help_text = _("please include as much information as possible..")
    feedback_url_help_text = _("provide the url when the trouble happens")

    uuid = models.CharField(max_length=36)
    title = models.TextField(
        _("Choose an area"),
        null=True,
        blank=True)
    details = models.TextField(
        _("Details"),
        null=True,
        blank=True,
        help_text=details_help_text)
    feedback_url = models.URLField(
      _("URL"),
      blank=True,
      null=True,
      max_length=255,
      help_text=feedback_url_help_text)
    feedback_file = models.FileField(
        upload_to=upload_to,
        null=True,
        blank=True,
        max_length=255,
        verbose_name=feedback_file_help_text)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    extension = models.CharField(max_length=128, blank=True, null=True)
    feedback_type = models.CharField(max_length=128, blank=True, null=True)
    created_date = models.DateTimeField(
        _('Created Date'),
        default=now)
    
    def __str__(self) -> str:
        return super().__str__(self.title)

    @property
    def name(self):
        if not self.title:
            return str(self.id)
        else:
            return self.title

    def find_placeholder(self):
        placeholder = 'feedbacks/{0}-placeholder.png'
        if finders.find(placeholder.format(self.extension), False):
            return finders.find(placeholder.format(self.extension), False)
        elif self.is_image:
            return finders.find(placeholder.format('image'), False)
        elif self.is_video:
            return finders.find(placeholder.format('video'), False)
        return finders.find(placeholder.format('generic'), False)

    # def save_feedback_file(self, filename, image):
    #     upload_path = get_unique_feedback_path(self, filename)

    #     try:
    #         if upload_path and image:
    #             actual_name = storage_manager.save(upload_path, ContentFile(image))
    #             actual_file_name = os.path.basename(actual_name)
    #             if filename != actual_file_name:
    #                 upload_path = upload_path.replace(filename, actual_file_name)
    #             url = storage_manager.url(upload_path)

    #     except Exception as e:
    #         logger.error(
    #             f'Error when saving the feedback for resource {self.id}. ({e})')


# def post_save_feedback(instance, sender, **kwargs):
#     from .tasks import create_feedback

#     base_name, extension = os.path.splitext(instance.feedback_file.name)
#     ext = extension[1:]
#     feedback_type_map = DOCUMENT_TYPE_MAP
#     feedback_type_map.update(getattr(settings, 'DOCUMENT_TYPE_MAP', {}))

#     if instance.id and instance.feedback_file:
#         create_feedback.apply_sync((instance.id,))

#     if feedback_type_map is None:
#         feedback_type = 'other'
#     else:
#         feedback_type = feedback_type_map.get(ext.lower(), 'other')
#     feedback_type = feedback_type

#     if instance.uuid is None or instance.uuid == '':
#         instance.uuid  = str(uuid.uuid1())

#     if ext:
#         Feedback.objects.get_or_create(
#             extension=ext,
#             feedback_type=feedback_type)

# signals.post_save.connect(post_save_feedback, sender=Feedback)