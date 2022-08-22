from django.utils.translation import ugettext_noop as _
from geonode.notifications_helper import NotificationsAppConfigBase


class DatasetsAppConfig(NotificationsAppConfigBase):
    name = 'geonode.datasets'
    NOTIFICATIONS = (("dataset_created", _("Dataset Created"), _("A Dataset was created"),),
                     ("dataset_updated", _("Dataset Updated"), _("A Dataset was updated"),),
                     ("dataset_approved", _("Dataset Approved"), _("A Dataset was approved by a Manager"),),
                     ("dataset_published", _("Dataset Published"), _("A Dataset was published"),),
                     ("dataset_deleted", _("Dataset Deleted"), _("A Dataset was deleted"),),
                     ("dataset_comment", _("Comment on Dataset"), _("A Dataset was commented on"),),
                     ("dataset_rated", _("Rating for Dataset"), _("A rating was given to a dataset"),),
                     )
    verbose_name = 'Datasets'


default_app_config = 'geonode.datasets.DatasetsAppConfig'
