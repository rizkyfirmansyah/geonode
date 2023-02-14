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

    @extend_schema(
        methods=['post'],
        responses={200},
        description="API endpoint to checking features of spatial data; should load the button?"
    )
    @action(
        detail=False,
        url_path="check_features/(?P<resource_id>\d+)?$",
        url_name="check_features",
        methods=['post'],
        permission_classes=[
            IsAuthenticated
        ],
        parser_classes=[JSONParser, FormParser]
    )
    def check_features(self, request, resource_id):
        from psycopg2 import connect
        from urllib.parse import urlparse
        from django.contrib import messages
        from django.utils.translation import ugettext as _
        def _check_by_limit(table, limit):
            """
            perform query to each layers in order to display on layer detail page as datatables
            connect to geodatabase defined in the .env using psycopg2
            return: json attributes omitted the_geom column and fid
            """

            def _query_set(table, limit):
                query = 'select count(*), count(*) > ' + str(limit) + ' as data from ' + table + ''
                return query

            def _connect():
                result = urlparse(settings.GEODATABASE_URL)
                username = result.username
                password = result.password
                database = result.path[1:]
                hostname = result.hostname
                port = result.port
                try:
                    connection = connect(
                        database=database,
                        user=username,
                        password=password,
                        host=hostname,
                        port=port
                    )
                except Exception as err:
                    print(f"Stacktrace error connecting database: {str(err)}")
                    connection = None
                return connection

            conn = _connect()
            if conn != None:
                cursor = conn.cursor()
                try:
                    cursor.execute(_query_set(table, limit))
                    query_results = cursor.fetchone()

                    return query_results
                except Exception as err:
                    print(f"Stacktrace error connecting database: {str(err)}")
                finally:
                    # close the cursor object to avoid memory leak
                    cursor.close()
                    # then close the connection object
                    conn.close()


                layer = Layer.objects.get(id=resource_id)
                data_tables = _check_by_limit(layer.name, settings.LIMIT_FEATURE_LAYERS)
                # if callback is true, display the toast info
                load_feature = data_tables[1]
                total_feature = data_tables[0]

                return Response({'data': load_feature,'total': total_feature })
            else:
                return Response({'data': "Error connecting database, please contact your Administrator"}, status=500, exception=True)