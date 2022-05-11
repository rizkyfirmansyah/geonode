from django.apps import AppConfig


class DatasetsConfig(AppConfig):
    name = 'geonode.datasets'
    verbose_name = 'Datasets'


default_app_config = 'geonode.datasets.DatasetsConfig'
