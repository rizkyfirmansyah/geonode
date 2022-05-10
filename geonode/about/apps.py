from django.apps import AppConfig as BaseAppConfig
from django.utils.translation import ugettext_lazy as _


class AboutConfig(BaseAppConfig):
    name = 'geonode.about'
    verbose_name = _("Help & About Site")
