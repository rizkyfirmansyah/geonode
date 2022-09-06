from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _

from django.db.models import signals
from django.urls import reverse
from django.utils.functional import classproperty
from geonode.datasets.enumerations import DATASET_TYPE_MAP, DOCUMENT_MIMETYPE_MAP
from geonode.security.permissions import (
    VIEW_PERMISSIONS,
    OWNER_PERMISSIONS,
    DOWNLOAD_PERMISSIONS)
from geonode.groups.conf import settings as groups_settings
from geonode.maps.models import Map
from geonode.layers.models import Layer
from django.contrib.staticfiles import finders
from urllib.parse import urljoin
from geonode.utils import build_absolute_uri
from geonode.base.models import ResourceBase
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from geonode.storage.manager import storage_manager
import logging
from geonode.client.hooks import hookset

logger = logging.getLogger(__name__)

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

class Dataset(ResourceBase):

    """
    A dataset is any kind of information that can be attached to a map such as pdf, images, videos, xls...
    """

    def __str__(self):
        return str(self.title)

    def get_absolute_url(self):
        return hookset.dataset_detail_url(self)

    @classproperty
    def allowed_permissions(cls):
        return {
            "anonymous": VIEW_PERMISSIONS,
            "default": OWNER_PERMISSIONS + DOWNLOAD_PERMISSIONS,
            groups_settings.REGISTERED_MEMBERS_GROUP_NAME: OWNER_PERMISSIONS + DOWNLOAD_PERMISSIONS
        }

    @classproperty
    def compact_permission_labels(cls):
        return {
            "none": _("None"),
            "view": _("View Metadata"),
            "download": _("View and Download"),
            "edit": _("Edit"),
            "manage": _("Manage"),
            "owner": _("Owner")
        }

    @property
    def name(self):
        if not self.title:
            return str(self.id)
        else:
            return self.title

    @property
    def name_long(self):
        if not self.title:
            return str(self.id)
        else:
            return f'{self.title} ({self.id})'


    class Meta(ResourceBase.Meta):
        pass


class File(models.Model):

    """
    A document is any kind of information that can be attached to a map such as pdf, images, videos, xls...
    """
    dataset = models.ForeignKey(Dataset, blank=True, null=True, on_delete=models.CASCADE)
    import_id = models.BigIntegerField(null=True)
    file_name = models.CharField(max_length=255, null=False, blank=False)
    file_description = models.TextField(
        default='',
        blank=True,
        null=True
    )
    file_data_quality = models.TextField(
        _('Data Quality Statement'),
        max_length=2000,
        blank=True,
        null=True,
        help_text=ResourceBase.data_quality_statement_help_text)

    file = models.TextField(
        null=True,
        blank=True,
        verbose_name=_('File'))

    file_size = models.PositiveBigIntegerField(default=0)

    extension = models.CharField(max_length=128, blank=True, null=True)
    file_type = models.CharField(max_length=128, blank=True, null=True)
    file_url = models.URLField(
        blank=True,
        null=True,
        max_length=2000,
        help_text=_('The URL of the document if it is external.'),
        verbose_name=_('URL'))
    hash = models.TextField(null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    last_updated = models.DateTimeField(auto_now=True, null=True, blank=True)
    session = models.TextField(null=True, blank=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.file_name)

    @classproperty
    def allowed_permissions(cls):
        return {
            "anonymous": VIEW_PERMISSIONS + DOWNLOAD_PERMISSIONS,
            "default": OWNER_PERMISSIONS + DOWNLOAD_PERMISSIONS,
            groups_settings.REGISTERED_MEMBERS_GROUP_NAME: OWNER_PERMISSIONS + DOWNLOAD_PERMISSIONS
        }

    @classproperty
    def compact_permission_labels(cls):
        return {
            "none": _("None"),
            "view": _("View Metadata"),
            "download": _("View and Download"),
            "edit": _("Edit"),
            "manage": _("Manage"),
            "owner": _("Owner")
        }

    @property
    def name(self):
        if not self.file_name:
            return str(self.id)
        else:
            return self.file_name

    @property
    def name_long(self):
        if not self.file_name:
            return str(self.id)
        else:
            return f'{self.file_name} ({self.id})'

    @property
    def href(self):
        if self.doc_url:
            return self.doc_url
        elif self.file:
            return urljoin(
                settings.SITEURL,
                reverse('dataset_link', args=(self.id,))
            )

    @property
    def is_file(self):
        return self.file and self.extension

    @property
    def mime_type(self):
        if self.is_file and self.extension.lower() in DOCUMENT_MIMETYPE_MAP:
            return DOCUMENT_MIMETYPE_MAP[self.extension.lower()]
        return None

    @property
    def is_audio(self):
        AUDIOTYPES = [_e for _e, _t in DATASET_TYPE_MAP.items() if _t == 'audio']
        return self.is_file and self.extension.lower() in AUDIOTYPES

    @property
    def is_image(self):
        IMGTYPES = [_e for _e, _t in DATASET_TYPE_MAP.items() if _t == 'image']
        return self.is_file and self.extension.lower() in IMGTYPES

    @property
    def is_video(self):
        VIDEOTYPES = [_e for _e, _t in DATASET_TYPE_MAP.items() if _t == 'video']
        return self.is_file and self.extension.lower() in VIDEOTYPES


    @property
    def is_tabular(self):
        TABULARTYPES = [_e for _e, _t in DATASET_TYPE_MAP.items() if _t == 'tabular']
        return self.is_file and self.extension.lower() in TABULARTYPES

    @property
    def class_name(self):
        return self.__class__.__name__

    @property
    def embed_url(self):
        return reverse('dataset_embed', args=(self.id,))

    @property
    def download_url(self):
        return build_absolute_uri(reverse('dataset_download', args=(self.id,)))

    class Meta:
        permissions = (
            ('preview_file', 'Can preview file'),
            ('download_file', 'Can download file'),
        )


class FileResourceLink(models.Model):

    # relation to the document model
    document = models.ForeignKey(
        Dataset,
        null=True,
        blank=True,
        related_name='links',
        on_delete=models.CASCADE)

    # relation to the resource model
    content_type = models.ForeignKey(
        ContentType,
        null=True,
        blank=True,
        on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    resource = GenericForeignKey('content_type', 'object_id')


def get_related_datasets(resource):
    if isinstance(resource, Layer) or isinstance(resource, Map):
        content_type = ContentType.objects.get_for_model(resource)
        return Dataset.objects.filter(links__content_type=content_type,
                                       links__object_id=resource.pk)
    else:
        return None


def auto_delete_file_on_delete(sender, instance, **kwargs):
    """
    Deletes file from filesystem
    when corresponding `File` object is deleted.
    """
    if instance.file:
        logger.debug(
            f"Going to delete associated file for {instance.name}"
        )
        storage_manager.delete(instance.file)


signals.pre_delete.connect(auto_delete_file_on_delete, sender=File)