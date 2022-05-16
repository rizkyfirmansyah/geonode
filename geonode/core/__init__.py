from django.apps import AppConfig


class CoreConfig(AppConfig):
    name = 'geonode.core'
    verbose_name = 'core'


default_app_config = 'geonode.core.CoreConfig'