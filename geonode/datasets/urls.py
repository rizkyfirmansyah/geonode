# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2016 OSGeo
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
#########################################################################
from django.conf.urls import url, include
from django.views.generic import TemplateView
from django.conf.urls.static import static
from django.conf import settings

from .api.views import DatasetIngestDetailView, DatasetIngestView

from .views import DatasetUploadView, DatasetUpdateView
from .views import DatasetAutocomplete
from . import views
from geonode.base import register_url_event
from geonode.decorators import registered_users

js_info_dict = {
    'packages': ('geonode.datasets',),
}

datasets_list = register_url_event()(TemplateView.as_view(
        template_name='datasets/dataset_list.html'))

urlpatterns = [  # 'geonode.datasets.views',
    url(r'^$',
        registered_users(datasets_list),
        {'facet_type': 'datasets'},
        name='dataset_browse'
        ),
    url(r'^(?P<docid>\d+)/tabular$',
        views.render_tabular, name='render_tabular'),
    url(r'^(?P<docid>\d+)/?$',
        views.dataset_detail, name='dataset_detail'),
    # url(r'^(?P<docid>\d+)/download/?$',
    #     views.dataset_download, name='dataset_download'),
    url(r'^file/download$',
        views.dataset_download, name='dataset_download'),
    url(r'^(?P<docid>\d+)/link/?$',
        views.dataset_link, name='dataset_link'),
    # url(r'^file/link$',
    #     views.dataset_link, name='dataset_link'),
    url(r'^(?P<docid>\d+)/replace$', DatasetUpdateView.as_view(),
        name="dataset_replace"),
    url(r'^(?P<docid>\d+)/embed/?$',
        views.dataset_embed, name='dataset_embed'),
    url(r'^remove$',
        views.dataset_remove, name="dataset_remove"),
    url(r'^upload/?$', DatasetUploadView.as_view(), name='dataset_upload'),
    # url(r'^upload/(?P<filename>[^/]+)$', DatasetIngestView.as_view(), name='dataset_ingest'),
    url(r'^upload/file$', DatasetIngestView.as_view({'post': 'post'}), name='dataset_ingest'),
    url(r'^upload/file/preview/(?P<pk>[0-9]+)$', DatasetIngestView.as_view({'get': 'preview_file'}), name='dataset_ingest_preview_file'),
    # url(r'^upload/file$', DatasetIngestView.as_view(), name='dataset_ingest'),
    url(r'^upload/file/(?P<pk>[0-9]+)$', DatasetIngestDetailView.as_view(), name='dataset_ingest_detail'),
    url(r'^(?P<docid>[^/]*)/metadata_detail$', views.dataset_metadata_detail,
        name='dataset_metadata_detail'),
    url(r'^(?P<docid>\d+)/metadata$',
        views.dataset_metadata, name='dataset_metadata'),
    url(r'^metadata/batch/$',
        views.dataset_batch_metadata, name='dataset_batch_metadata'),
    url(r'^(?P<docid>\d+)/metadata_advanced$', views.dataset_metadata_advanced,
        name='dataset_metadata_advanced'),
    url(r'^permissions/batch/$',
        views.dataset_batch_permissions, name='dataset_batch_permissions'),
    url(r'^autocomplete/$',
        DatasetAutocomplete.as_view(), name='autocomplete_document'),
    url(r'^', include('geonode.datasets.api.urls')),
]
