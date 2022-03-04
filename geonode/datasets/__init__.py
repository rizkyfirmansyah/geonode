from django.apps import AppConfig


class DatasetsConfig(AppConfig):
    name = 'geonode.datasets'
    verbose_name = 'Datasets/ROPA'


default_app_config = 'geonode.datasets.DatasetsConfig'