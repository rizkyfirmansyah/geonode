# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2020 OSGeo
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
from dynamic_rest.viewsets import DynamicModelViewSet
from dynamic_rest.filters import DynamicFilterBackend, DynamicSortingFilter

from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.parsers import JSONParser, FormParser
from oauth2_provider.contrib.rest_framework import OAuth2Authentication

from geonode.base.api.filters import DynamicSearchFilter, ExtentFilter
from geonode.base.api.permissions import TokenAuthOAuthApplicationsQuery, UserHasPerms
from geonode.base.api.pagination import GeoNodeApiPagination
from geonode.layers.models import Layer
from geonode.layers.views import preview_data_tables
from django.conf import settings

from .serializers import LayerSerializer
from .permissions import LayerPermissionsFilter

import logging

logger = logging.getLogger(__name__)


class LayerViewSet(DynamicModelViewSet):
    """
    API endpoint that allows layers to be viewed or edited.
    """
    authentication_classes = [SessionAuthentication, BasicAuthentication, OAuth2Authentication]
    permission_classes = [TokenAuthOAuthApplicationsQuery | IsAuthenticated, UserHasPerms, ]

    filter_backends = [
        DynamicFilterBackend, DynamicSortingFilter, DynamicSearchFilter,
        ExtentFilter, LayerPermissionsFilter
    ]
    queryset = Layer.objects.all()
    serializer_class = LayerSerializer
    pagination_class = GeoNodeApiPagination

    @extend_schema(
        methods=['post'],
        responses={200},
        description="API endpoint to load all features of spatial data."
    )
    @action(
        detail=False,
        url_path="load_features/(?P<resource_id>\d+)?$",
        url_name="load_features",
        methods=['post'],
        permission_classes=[
            IsAuthenticated
        ],
        parser_classes=[JSONParser, FormParser]
    )
    def load_features(self, request, resource_id):
        layer = Layer.objects.get(id=resource_id)
        data_tables = preview_data_tables(layer.name, False)
        
        return Response({'data': data_tables[0].get('data'), 'total': data_tables[0].get('total_rows')})
