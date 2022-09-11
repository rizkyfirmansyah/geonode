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
import ast
import re
import json
from PIL import Image
from decimal import Decimal
from urllib.parse import urljoin, urlparse

from django.apps import apps
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from django.db.models import Subquery
from django.contrib import messages
from django.urls import reverse
from django_filters.rest_framework import DjangoFilterBackend
from django.core.validators import URLValidator
from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponseForbidden
from django.db import models

from geonode.thumbs.exceptions import ThumbnailError
from geonode.thumbs.thumbnails import create_thumbnail
from geonode.resource.api.tasks import resouce_service_dispatcher

from oauth2_provider.contrib.rest_framework import OAuth2Authentication

from dynamic_rest.viewsets import DynamicModelViewSet, WithDynamicViewSetMixin
from dynamic_rest.filters import DynamicFilterBackend, DynamicSortingFilter

from drf_spectacular.utils import extend_schema

from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from rest_framework.exceptions import ValidationError
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
from rest_framework.viewsets import GenericViewSet
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework import status

from geonode.base.models import Configuration, ExtraMetadata, HierarchicalKeyword, Region, ResourceBase, ResourceVersion, TopicCategory, DataType, ThesaurusKeyword
from geonode.base.api.filters import DynamicSearchFilter, ExtentFilter, ResourceBaseFilter
from geonode.base.utils import validate_extra_metadata
from geonode.favorite.models import Favorite
from geonode.groups.models import GroupProfile, GroupMember
from geonode.layers.models import Layer
from geonode.maps.models import Map
from geonode.groups.conf import settings as groups_settings
from geonode.security.utils import get_visible_resources, get_resources_with_perms
from geonode.security.permissions import PermSpec, PermSpecCompact, get_compact_perms_list
from geonode.resource.models import ExecutionRequest
from geonode.resource.manager import resource_manager
from geonode.thumbs.utils import _decode_base64, BASE64_PATTERN

from pinax.ratings.categories import category_value
from pinax.ratings.models import OverallRating, Rating
from pinax.ratings.views import NUM_OF_RATINGS

from guardian.shortcuts import get_objects_for_user

from .permissions import (
    IsSelfOrAdmin,
    IsOwnerOrAdmin,
    IsOwnerOrReadOnly,
    ResourceBasePermissionsFilter
)
from .serializers import (
    FavoriteSerializer,
    ResourceVersionChangesSerializer,
    ResourceVersionCreateSerializer,
    ResourceVersionSerializer,
    UserSerializer,
    PermSpecSerialiazer,
    GroupProfileSerializer,
    ResourceBaseSerializer,
    SimpleResourceBaseSerializer,
    ResourceBaseTypesSerializer,
    OwnerSerializer,
    HierarchicalKeywordSerializer,
    TopicCategorySerializer,
    DataTypeSerializer,
    RegionSerializer,
    ThesaurusKeywordSerializer,
    ExtraMetadataSerializer
)
from .pagination import GeoNodeApiPagination

import logging

logger = logging.getLogger(__name__)


class UserViewSet(DynamicModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    authentication_classes = [SessionAuthentication, BasicAuthentication, OAuth2Authentication]
    permission_classes = [IsSelfOrAdmin, ]
    queryset = get_user_model().objects.all()
    serializer_class = UserSerializer
    pagination_class = GeoNodeApiPagination

    def get_queryset(self):
        """
        Filter objects so a user only sees his own stuff.
        If user is admin, let him see all.
        """
        if self.request.user.is_superuser or self.request.user.is_staff:
            queryset = get_user_model().objects.all()
        else:
            queryset = get_user_model().objects.filter(id=self.request.user.id)
        # Set up eager loading to avoid N+1 selects
        queryset = self.get_serializer_class().setup_eager_loading(queryset)
        return queryset.order_by("username")

    @extend_schema(methods=['get'], responses={200: ResourceBaseSerializer(many=True)},
                   description="API endpoint allowing to retrieve the Resources visible to the user.")
    @action(detail=True, methods=['get'])
    def resources(self, request, pk=None):
        user = self.get_object()
        permitted = get_objects_for_user(user, 'base.view_resourcebase')
        qs = ResourceBase.objects.all().filter(id__in=permitted).order_by('title')

        resources = get_visible_resources(
            qs,
            user,
            admin_approval_required=settings.ADMIN_MODERATE_UPLOADS,
            unpublished_not_visible=settings.RESOURCE_PUBLISHING,
            private_groups_not_visibile=settings.GROUP_PRIVATE_RESOURCES)
        return Response(ResourceBaseSerializer(embed=True, many=True).to_representation(resources))

    @extend_schema(methods=['get'], responses={200: GroupProfileSerializer(many=True)},
                   description="API endpoint allowing to retrieve the Groups the user is member of.")
    @action(detail=True, methods=['get'])
    def groups(self, request, pk=None):
        user = self.get_object()
        qs_ids = GroupMember.objects.filter(user=user).values_list("group", flat=True)
        groups = GroupProfile.objects.filter(id__in=qs_ids)
        return Response(GroupProfileSerializer(embed=True, many=True).to_representation(groups))


class GroupViewSet(DynamicModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    authentication_classes = [SessionAuthentication, BasicAuthentication, OAuth2Authentication]
    permission_classes = [IsAuthenticated, ]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['slug', 'title', 'categories']
    serializer_class = GroupProfileSerializer
    pagination_class = GeoNodeApiPagination

    def get_queryset(self):
        queryset = GroupProfile.objects.all()
        slug = self.request.query_params.get('q', None)
        if slug is not None:
            queryset = queryset.filter(slug__icontains=slug)
        return queryset

    @extend_schema(methods=['get'], responses={200: UserSerializer(many=True)},
                   description="API endpoint allowing to retrieve the Group members.")
    @action(detail=True, methods=['get'])
    def members(self, request, pk=None):
        group = self.get_object()
        members = get_user_model().objects.filter(id__in=group.member_queryset().values_list("user", flat=True))
        return Response(data={"resources":UserSerializer(embed=True, many=True).to_representation(members)})

    @extend_schema(methods=['get'], responses={200: UserSerializer(many=True)},
                   description="API endpoint allowing to retrieve the Group managers.")
    @action(detail=True, methods=['get'])
    def managers(self, request, pk=None):
        group = self.get_object()
        managers = group.get_managers()
        return Response(UserSerializer(embed=True, many=True).to_representation(managers))

    @extend_schema(methods=['get'], responses={200: ResourceBaseSerializer(many=True)},
                   description="API endpoint allowing to retrieve the Group specific resources.")
    @action(detail=True, methods=['get'])
    def resources(self, request, pk=None):
        group = self.get_object()
        resources = group.resources()
        return Response(ResourceBaseSerializer(embed=True, many=True).to_representation(resources))


class RegionViewSet(WithDynamicViewSetMixin, ListModelMixin, RetrieveModelMixin, GenericViewSet):
    """
    API endpoint that lists regions.
    """
    if settings.DEFAULT_ANONYMOUS_ACCESS_PERMISSION:
        permission_classes = [AllowAny, ]
    else:
        permission_classes = [IsAuthenticated, ]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['name', 'code']
    serializer_class = RegionSerializer
    pagination_class = GeoNodeApiPagination

    def get_queryset(self):
        queryset = Region.objects.all()
        name = self.request.query_params.get('q', None)
        if name is not None:
            queryset = queryset.filter(name__icontains=name)
        return queryset


class HierarchicalKeywordViewSet(WithDynamicViewSetMixin, ListModelMixin, RetrieveModelMixin, GenericViewSet):
    """
    API endpoint that lists hierarchical keywords.
    """
    if settings.DEFAULT_ANONYMOUS_ACCESS_PERMISSION:
        permission_classes = [AllowAny, ]
    else:
        permission_classes = [IsAuthenticated, ]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['slug', 'name']
    serializer_class = HierarchicalKeywordSerializer
    pagination_class = GeoNodeApiPagination

    def get_queryset(self):
        queryset = HierarchicalKeyword.objects.all()
        slug = self.request.query_params.get('q', None)
        if slug is not None:
            queryset = queryset.filter(slug__icontains=slug)
        return queryset


class ThesaurusKeywordViewSet(WithDynamicViewSetMixin, ListModelMixin, RetrieveModelMixin, GenericViewSet):
    """
    API endpoint that lists Thesaurus keywords.
    """
    if settings.DEFAULT_ANONYMOUS_ACCESS_PERMISSION:
        permission_classes = [AllowAny, ]
    else:
        permission_classes = [IsAuthenticated, ]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['id', 'thesaurus', 'alt_label']
    serializer_class = ThesaurusKeywordSerializer
    pagination_class = GeoNodeApiPagination

    def get_queryset(self):
        queryset = ThesaurusKeyword.objects.all()
        id = self.request.query_params.get('q', None)
        if id is not None:
            queryset = queryset.filter(id=id)
        return queryset


class TopicCategoryViewSet(WithDynamicViewSetMixin, ListModelMixin, RetrieveModelMixin, GenericViewSet):
    """
    API endpoint that lists categories.
    """
    if settings.DEFAULT_ANONYMOUS_ACCESS_PERMISSION:
        permission_classes = [AllowAny, ]
    else:
        permission_classes = [IsAuthenticated, ]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['identifier', 'title']
    serializer_class = TopicCategorySerializer
    pagination_class = GeoNodeApiPagination

    def get_queryset(self):
        queryset = TopicCategory.objects.all()
        identifier = self.request.query_params.get('q', None)
        if identifier is not None:
            queryset = queryset.filter(identifier__icontains=identifier)
        return queryset


class DataTypeViewSet(WithDynamicViewSetMixin, ListModelMixin, RetrieveModelMixin, GenericViewSet):
    """
    API endpoint that lists data type.
    """
    if settings.DEFAULT_ANONYMOUS_ACCESS_PERMISSION:
        permission_classes = [AllowAny, ]
    else:
        permission_classes = [IsAuthenticated, ]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['identifier', 'title']
    serializer_class = DataTypeSerializer
    pagination_class = GeoNodeApiPagination

    def get_queryset(self):
        queryset = DataType.objects.all()
        identifier = self.request.query_params.get('q', None)
        if identifier is not None:
            queryset = queryset.filter(identifier__icontains=identifier)
        return queryset


class OwnerViewSet(WithDynamicViewSetMixin, ListModelMixin, RetrieveModelMixin, GenericViewSet):
    """
    API endpoint that lists all possible owners.
    """
    authentication_classes = [SessionAuthentication, BasicAuthentication, OAuth2Authentication]
    if settings.DEFAULT_ANONYMOUS_ACCESS_PERMISSION:
        permission_classes = [AllowAny, ]
    else:
        permission_classes = [IsAuthenticated, ]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['username', 'id']
    serializer_class = OwnerSerializer
    pagination_class = GeoNodeApiPagination

    def get_queryset(self):
        """
        Filter users with atleast a resource
        """
        queryset = get_user_model().objects.exclude(pk=-1)
        filter_options = {}
        if self.request.query_params:
            filter_options = {
                'type_filter': self.request.query_params.get('type'),
                'title_filter': self.request.query_params.get('title__icontains')
            }
        username = self.request.query_params.get('q', None)
        if username is not None:
            queryset = queryset.filter(username__icontains=username)
        else:
            queryset = queryset.filter(id__in=Subquery(
                get_resources_with_perms(self.request.user, filter_options).values('owner'))
            )

        return queryset.order_by("username")


class ResourceBasePermsViewSet(DynamicModelViewSet):
    """
    Minimize API endpoint to check user's permissions.
    """
    authentication_classes = [SessionAuthentication, BasicAuthentication, OAuth2Authentication]
    if settings.DEFAULT_ANONYMOUS_ACCESS_PERMISSION:
        permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    else:
        permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]

    queryset = ResourceBase.objects.all().order_by('-pk')
    serializer_class = SimpleResourceBaseSerializer


class ResourceBaseViewSet(DynamicModelViewSet):
    """
    API endpoint that allows base resources to be viewed or edited.
    """
    authentication_classes = [SessionAuthentication, BasicAuthentication, OAuth2Authentication]
    if settings.DEFAULT_ANONYMOUS_ACCESS_PERMISSION:
        permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    else:
        permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
    filter_backends = [
        DynamicFilterBackend, DynamicSortingFilter, DynamicSearchFilter,
        ExtentFilter, ResourceBasePermissionsFilter, ResourceBaseFilter
    ]
    serializer_class = ResourceBaseSerializer
    pagination_class = GeoNodeApiPagination
    ordering_fields = ('title', 'date', 'popular_count')
    ordering = ('-last_updated')

    def _filtered(self, request, filter):
        paginator = GeoNodeApiPagination()
        paginator.page_size = request.GET.get('page_size', 10)
        resources = get_resources_with_perms(request.user).filter(**filter)
        result_page = paginator.paginate_queryset(resources, request)
        serializer = ResourceBaseSerializer(result_page, embed=True, many=True)
        return paginator.get_paginated_response({"resources": serializer.data})

    @extend_schema(methods=['get'], responses={200: ResourceBaseSerializer(many=True)},
                   description="API endpoint allowing to retrieve the approved Resources.")
    @action(detail=False, methods=['get'])
    def approved(self, request):
        return self._filtered(request, {"is_approved": True})

    @extend_schema(methods=['get'], responses={200: ResourceBaseSerializer(many=True)},
                   description="API endpoint allowing to retrieve the published Resources.")
    @action(detail=False, methods=['get'])
    def published(self, request):
        return self._filtered(request, {"is_published": True})

    @extend_schema(methods=['get'], responses={200: ResourceBaseSerializer(many=True)},
                   description="API endpoint allowing to retrieve the featured Resources.")
    @action(detail=False, methods=['get'])
    def featured(self, request):
        return self._filtered(request, {"featured": True})

    @extend_schema(methods=['get'], responses={200: FavoriteSerializer(many=True)},
                   description="API endpoint allowing to retrieve the favorite Resources.")
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated, ])
    def favorites(self, request, pk=None):
        paginator = GeoNodeApiPagination()
        paginator.page_size = request.GET.get('page_size', 10)
        favorites = Favorite.objects.favorites_for_user(user=request.user)
        result_page = paginator.paginate_queryset(favorites, request)
        serializer = FavoriteSerializer(result_page, embed=True, many=True)
        return paginator.get_paginated_response({"favorites": serializer.data})

    @extend_schema(methods=['post', 'delete'], responses={200: FavoriteSerializer(many=True)},
                   description="API endpoint allowing to retrieve the favorite Resources.")
    @action(detail=True, methods=['post', 'delete'], permission_classes=[IsAuthenticated, ])
    def favorite(self, request, pk=None):
        resource = self.get_object()
        user = request.user

        if request.method == 'POST':
            try:
                Favorite.objects.get(user=user, object_id=resource.pk)
                return Response({"message": "Resource is already in favorites"}, status=400)
            except Favorite.DoesNotExist:
                Favorite.objects.create_favorite(resource, user)
                return Response({"message": "Successfuly added resource to favorites"}, status=201)

        if request.method == 'DELETE':
            try:
                Favorite.objects.get(user=user, object_id=resource.pk).delete()
                return Response({"message": "Successfuly removed resource from favorites"}, status=200)
            except Favorite.DoesNotExist:
                return Response({"message": "Resource not in favorites"}, status=404)

    @extend_schema(methods=['get'], responses={200: ResourceBaseTypesSerializer()},
                   description="""
        Returns the list of available ResourceBase polymorphic_ctypes.

        the mapping looks like:
        ```
        {
            "resource_types":[
                {
                    "name": "layer",
                    "count": <number of layers>
                },
                {
                    "name": "map",
                    "count": <number of maps>
                },
                {
                    "name": "dataset",
                    "count": <number of datasets>
                },
                {
                    "name": "geostory",
                    "count": <number of geostories>
                }
            ]
        }
        ```
        """)
    @action(detail=False, methods=['get'], url_name="resource_types",
        permission_classes=[
            IsAuthenticated,
        ],    
    )
    def resource_types(self, request):

        def _to_compact_perms_list(allowed_perms: dict, resource_type: str, resource_subtype: str, compact_perms_labels: dict = {}) -> list:
            _compact_perms_list = {}
            for _k, _v in allowed_perms.items():
                _is_owner = _k not in ["anonymous", groups_settings.REGISTERED_MEMBERS_GROUP_NAME]
                _is_none_allowed = not _is_owner
                _compact_perms_list[_k] = get_compact_perms_list(
                    _v,
                    resource_type,
                    resource_subtype,
                    _is_owner,
                    _is_none_allowed,
                    compact_perms_labels)
            return _compact_perms_list

        resource_types = []
        _types = []
        _allowed_perms = {}
        for _model in apps.get_models():
            if _model.__name__ == "ResourceBase":
                for _m in _model.__subclasses__():
                    if _m.__name__.lower() not in ['service']:
                        _types.append(_m.__name__.lower())
                        _allowed_perms[_m.__name__.lower()] = {
                            "perms": _m.allowed_permissions,
                            "compact": _to_compact_perms_list(
                                _m.allowed_permissions, _m.__name__.lower(), _m.__name__.lower(), _m.compact_permission_labels)
                        }

        if settings.GEONODE_APPS_ENABLE and 'geoapp' in _types:
            _types.remove('geoapp')
            if hasattr(settings, 'CLIENT_APP_LIST') and settings.CLIENT_APP_LIST:
                _types += settings.CLIENT_APP_LIST
            else:
                from geonode.geoapps.models import GeoApp
                geoapp_types = [x for x in GeoApp.objects.values_list('resource_type', flat=True).all().distinct()]
                _types += geoapp_types

            if hasattr(settings, 'CLIENT_APP_ALLOWED_PERMS_LIST') and settings.CLIENT_APP_ALLOWED_PERMS_LIST:
                for _type in settings.CLIENT_APP_ALLOWED_PERMS_LIST:
                    for _type_name, _type_perms in _type.items():
                        _compact_permission_labels = {}
                        if hasattr(settings, 'CLIENT_APP_COMPACT_PERM_LABELS'):
                            _compact_permission_labels = settings.CLIENT_APP_COMPACT_PERM_LABELS.get(_type_name, {})
                        _allowed_perms[_type_name] = {
                            "perms": _type_perms,
                            "compact": _to_compact_perms_list(_type_perms, _type_name, _type_name, _compact_permission_labels)
                        }
            else:
                from geonode.geoapps.models import GeoApp
                for _m in GeoApp.objects.filter(resource_type__in=_types).iterator():
                    if hasattr(_m, 'resource_type') and _m.resource_type and _m.resource_type not in _allowed_perms:
                        _allowed_perms[_m.resource_type] = {
                            "perms": _m.allowed_permissions,
                            "compact": _to_compact_perms_list(
                                _m.allowed_permissions, _m.resource_type, _m.subtype, _m.compact_permission_labels)
                        }

        for _type in _types:
            resource_types.append({
                "name": _type,
                "count": get_resources_with_perms(request.user).filter(resource_type=_type).count(),
                "allowed_perms": _allowed_perms[_type] if _type in _allowed_perms else []
            })
        return Response({"resource_types": resource_types})

    @extend_schema(methods=['get', 'put', 'patch', 'delete'],
                   request=PermSpecSerialiazer(),
                   responses={200: None},
                   description="""
        Sets an object's the permission levels based on the perm_spec JSON.

        the mapping looks like:
        ```
        {
            'users': {
                'AnonymousUser': ['view'],
                <username>: ['perm1','perm2','perm3'],
                <username2>: ['perm1','perm2','perm3']
                ...
            },
            'groups': {
                <groupname>: ['perm1','perm2','perm3'],
                <groupname2>: ['perm1','perm2','perm3'],
                ...
            }
        }
        ```
        """)
    @action(
        detail=True,
        url_path="permissions",  # noqa
        url_name="perms-spec",
        methods=['get', 'put', 'patch', 'delete'],
        permission_classes=[
            IsAuthenticated
        ])
    def resource_service_permissions(self, request, pk):
        """Instructs the Async dispatcher to execute a 'DELETE' or 'UPDATE' on the permissions of a valid 'uuid'

        - GET input_params: {
            id: "<str: ID>"
        }

        - DELETE input_params: {
            id: "<str: ID>"
        }

        - PUT input_params: {
            id: "<str: ID>"
            owner: str = None
            permissions: dict = {}
            created: bool = False
        }

        - output_params: {
            output: {
                uuid: "<str: UUID>"
            }
        }

        - output: {
                "status": "ready",
                "execution_id": "<str: execution ID>",
                "status_url": "http://localhost:8000/api/v2/resource-service/execution-status/<str: execution ID>"
            }

        Sample Requests:
        - Removes all the permissions (except owner and admin ones) from a Resource:
        curl -v -X DELETE -u admin:admin -H "Content-Type: application/json" http://localhost:8000/api/v2/resources/<id>/permissions

        - Changes the owner of a Resource:
            curl -u admin:admin --location --request PUT 'http://localhost:8000/api/v2/resources/<id>/permissions' \
                --header 'Content-Type: application/json' \
                --data-raw '{"groups": [],"organizations": [],"users": [{"id": 1001,"permissions": "owner"}]}'

        - Assigns View permissions to some users:
            curl -u admin:admin --location --request PUT 'http://localhost:8000/api/v2/resources/<id>/permissions' \
                --header 'Content-Type: application/json' \
                --data-raw '{"groups": [],"organizations": [],"users": [{"id": 1000,"permissions": "view"}]}'

        - Assigns View permissions to anyone:
            curl -u admin:admin --location --request PUT 'http://localhost:8000/api/v2/resources/<id>/permissions' \
                --header 'Content-Type: application/json' \
                --data-raw '{"groups": [],"organizations": [],"users": [{"id": -1,"permissions": "view"}]}'

        - Assigns View permissions to anyone and edit permissions to a Group on a Dataset:
            curl -u admin:admin --location --request PUT 'http://localhost:8000/api/v2/resources/<id>/permissions' \
                --header 'Content-Type: application/json' \
                --data-raw '{"groups": [{"id": 1,"permissions": "manage"}],"organizations": [],"users": [{"id": -1,"permissions": "view"}]}'

        """
        config = Configuration.load()
        resource = get_object_or_404(ResourceBase, pk=pk)
        _user_can_manage = request.user.has_perm('change_resourcebase_permissions', resource.get_self_resource())
        if config.read_only or config.maintenance or request.user.is_anonymous or not request.user.is_authenticated or \
                resource is None or not _user_can_manage:
            return Response(status=status.HTTP_403_FORBIDDEN)
        try:
            perms_spec = PermSpec(resource.get_all_level_info(), resource)
            request_params = request.data
            if request.method == 'GET':
                return Response(perms_spec.compact)
            elif request.method == 'DELETE':
                _exec_request = ExecutionRequest.objects.create(
                    user=request.user,
                    func_name='remove_permissions',
                    geonode_resource=resource,
                    action="permissions",
                    input_params={
                        "uuid": request_params.get('uuid', resource.uuid)
                    }
                )
            elif request.method == 'PUT':
                perms_spec_compact = PermSpecCompact(request.data, resource)
                _exec_request = ExecutionRequest.objects.create(
                    user=request.user,
                    func_name='set_permissions',
                    geonode_resource=resource,
                    action="permissions",
                    input_params={
                        "uuid": request_params.get('uuid', resource.uuid),
                        "owner": request_params.get('owner', resource.owner.username),
                        "permissions": perms_spec_compact.extended,
                        "created": request_params.get('created', False)
                    }
                )
            elif request.method == 'PATCH':
                perms_spec_compact_patch = PermSpecCompact(request.data, resource)
                perms_spec_compact_resource = PermSpecCompact(perms_spec.compact, resource)
                perms_spec_compact_resource.merge(perms_spec_compact_patch)
                _exec_request = ExecutionRequest.objects.create(
                    user=request.user,
                    func_name='set_permissions',
                    geonode_resource=resource,
                    action="permissions",
                    input_params={
                        "uuid": request_params.get('uuid', resource.uuid),
                        "owner": request_params.get('owner', resource.owner.username),
                        "permissions": perms_spec_compact_resource.extended,
                        "created": request_params.get('created', False)
                    }
                )
            resouce_service_dispatcher.apply_async((_exec_request.exec_id,))
            return Response(
                {
                    'status': _exec_request.status,
                    'execution_id': _exec_request.exec_id,
                    'status_url':
                        urljoin(
                            settings.SITEURL,
                            reverse('rs-execution-status', kwargs={'execution_id': _exec_request.exec_id})
                        )
                },
                status=status.HTTP_200_OK)
        except Exception as e:
            logger.exception(e)
            return Response(status=status.HTTP_400_BAD_REQUEST, exception=e)


    @extend_schema(methods=['get'], responses={200: PermSpecSerialiazer()},
                   description="""
        Gets an object's the permission levels based on the perm_spec JSON.

        the mapping looks like:
        ```
        {
            'users': [
                'AnonymousUser': ['view'],
                <username>: ['perm1','perm2','perm3'],
                <username2>: ['perm1','perm2','perm3']
                ...
            ],
            'groups': [
                <groupname>: ['perm1','perm2','perm3'],
                <groupname2>: ['perm1','perm2','perm3'],
                ...
            ]
        }
        ```
        """)
    @action(detail=True, methods=['get'], permission_classes=[IsOwnerOrAdmin, ])
    def get_perms(self, request, pk=None):
        resource = self.get_object()
        perms_spec = resource.get_all_level_info()
        perms_spec_obj = {}
        if "users" in perms_spec:
            perms_spec_obj["users"] = {}
            for user in perms_spec["users"]:
                perms = perms_spec["users"].get(user)
                perms_spec_obj["users"][str(user)] = perms
        if "groups" in perms_spec:
            perms_spec_obj["groups"] = {}
            for group in perms_spec["groups"]:
                perms = perms_spec["groups"].get(group)
                perms_spec_obj["groups"][str(group)] = perms
        return Response(perms_spec_obj)

    @extend_schema(methods=['put'],
                   request=PermSpecSerialiazer(),
                   responses={200: None},
                   description="""
        Sets an object's the permission levels based on the perm_spec JSON.

        the mapping looks like:
        ```
        {
            'users': [
                'AnonymousUser': ['view'],
                <username>: ['perm1','perm2','perm3'],
                <username2>: ['perm1','perm2','perm3']
                ...
            ],
            'groups': [
                <groupname>: ['perm1','perm2','perm3'],
                <groupname2>: ['perm1','perm2','perm3'],
                ...
            ]
        }
        ```
        """)
    @action(detail=True, methods=['put'], permission_classes=[IsOwnerOrAdmin, ])
    def set_perms(self, request, pk=None):
        resource = self.get_object()
        resource.set_permissions(request.data)
        return Response(request.data)

    @extend_schema(
        methods=["post"], responses={200}, description="API endpoint allowing to set the thumbnail url for an existing dataset."
    )
    @action(
        detail=False,
        url_path="(?P<resource_id>\d+)/set_thumbnail_from_bbox",  # noqa
        url_name="set-thumb-from-bbox",
        methods=["post"],
        permission_classes=[
            IsAuthenticated,
        ],
    )
    def set_thumbnail_from_bbox(self, request, resource_id):
        import traceback
        from django.utils.datastructures import MultiValueDictKeyError
        toast_title = f"Update Thumbnail"
        
        try:
            resource = ResourceBase.objects.get(id=ast.literal_eval(resource_id))

            if not isinstance(resource.get_real_instance(), (Layer, Map)):
                raise NotImplementedError("Not implemented: Endpoint available only for Dataset and Maps")

            request_body = request.data if request.data else json.loads(request.body)
            try:
                bbox = request_body["bbox"] + [request_body["srid"]]
                zoom = request_body.get("zoom", None)
            except MultiValueDictKeyError:
                for _k, _v in request_body.items():
                    request_body = json.loads(_k)
                    break
                bbox = request_body["bbox"] + [request_body["srid"]]
                zoom = request_body.get("zoom", None)

            thumbnail_url = create_thumbnail(resource.get_real_instance(), bbox=bbox, background_zoom=zoom, overwrite=True)
            msg = f"Thumbnail correctly created."
            messages.success(request, message=msg, extra_tags=toast_title)

            return Response({"message": msg, "success": True, "thumbnail_url": thumbnail_url}, status=200)
        except ResourceBase.DoesNotExist:
            traceback.print_exc()
            msg = f"Resource selected with id {resource_id} does not exists"
            logger.error(msg)
            messages.error(request, message=msg, extra_tags=toast_title)

            return Response(
                data={"message": msg, "success": False}, status=404, exception=True)
        except NotImplementedError as e:
            traceback.print_exc()
            logger.error(e)
            messages.error(request, message=e.args[0], extra_tags=toast_title)

            return Response(data={"message": e.args[0], "success": False}, status=405, exception=True)
        except ThumbnailError as e:
            traceback.print_exc()
            logger.error(e)
            messages.error(request, message=e.args[0], extra_tags=toast_title)

            return Response(data={"message": e.args[0], "success": False}, status=500, exception=True)
        except Exception as e:
            traceback.print_exc()
            logger.error(e)
            messages.error(request, message=e.args[0], extra_tags=toast_title)

            return Response(data={"message": e.args[0], "success": False}, status=500, exception=True)

    @extend_schema(
        methods=['post', 'get'],
        responses={200},
        description="API endpoint allowing to rate and get overall rating of the Resource.")
    @action(
        detail=True,
        url_path="ratings",
        url_name="ratings",
        methods=['post', 'get'],
        permission_classes=[
            IsAuthenticatedOrReadOnly,
        ])
    def ratings(self, request, pk=None):
        resource = self.get_object()
        resource = resource.get_real_instance()
        ct = ContentType.objects.get_for_model(resource)
        if request.method == 'POST':
            rating_input = int(request.data.get("rating"))
            category = resource._meta.object_name.lower()
            # check if category is configured in settings.PINAX_RATINGS_CATEGORY_CHOICES
            cat_choice = category_value(resource, category)

            # Check for errors and bail early
            if category and cat_choice is None:
                return HttpResponseForbidden(
                    "Invalid category. It must match a preconfigured setting"
                )
            if rating_input not in range(NUM_OF_RATINGS + 1):
                return HttpResponseForbidden(
                    f"Invalid rating. It must be a value between 0 and {NUM_OF_RATINGS}"
                )
            Rating.update(
                rating_object=resource,
                user=request.user,
                category=cat_choice,
                rating=rating_input
            )
        user_rating = None
        if request.user.is_authenticated:
            user_rating = Rating.objects.filter(
                object_id=resource.pk,
                content_type=ct,
                user=request.user
            ).first()
        overall_rating = OverallRating.objects.filter(
            object_id=resource.pk,
            content_type=ct
        ).aggregate(r=models.Avg("rating"))["r"]
        overall_rating = Decimal(str(overall_rating or "0"))

        return Response(
            {
                "rating": user_rating.rating if user_rating else 0,
                "overall_rating": overall_rating
            }
        )

    @extend_schema(
        methods=['put'],
        responses={200},
        description="API endpoint allowing to set thumbnail of the Resource.")
    @action(
        detail=True,
        url_path="set_thumbnail",
        url_name="set_thumbnail",
        methods=['put'],
        permission_classes=[
            IsAuthenticated,
        ],
        parser_classes=[JSONParser, MultiPartParser]
    )
    def set_thumbnail(self, request, pk=None):
        resource = get_object_or_404(ResourceBase, pk=pk)

        if not request.data.get('file'):
            raise ValidationError("Field file is required")

        file_data = request.data['file']

        if isinstance(file_data, str):
            if re.match(BASE64_PATTERN, file_data):
                try:
                    thumbnail, _thumbnail_format = _decode_base64(file_data)
                except Exception:
                    return Response(
                        'The request body is not a valid base64 string or the image format is not PNG or JPEG',
                        status=status.HTTP_400_BAD_REQUEST
                    )
            else:
                try:
                    # Check if file_data is a valid url and set it as thumbail_url
                    validate = URLValidator()
                    validate(file_data)
                    if urlparse(file_data).path.rsplit('.')[-1] not in ['png', 'jpeg', 'jpg']:
                        return Response(
                            'The url must be of an image with format (png, jpeg or jpg)',
                            status=status.HTTP_400_BAD_REQUEST
                        )
                    resource.thumbnail_url = file_data
                    resource.save()
                    return Response({"thumbnail_url": resource.thumbnail_url})
                except Exception:
                    raise ValidationError(detail='file is either a file upload, ASCII byte string or a valid image url string')
        else:
            # Validate size
            if file_data.size > 1000000:
                raise ValidationError(detail='File must not exceed 1MB')

            thumbnail = file_data.read()
            try:
                file_data.seek(0)
                Image.open(file_data)
            except Exception:
                raise ValidationError(detail='Invalid data provided')
        if thumbnail:
            resource_manager.set_thumbnail(resource.uuid, instance=resource, thumbnail=thumbnail)
            return Response({"thumbnail_url": resource.thumbnail_url})
        return Response(
            'Unable to set thumbnail',
            status=status.HTTP_400_BAD_REQUEST
        )

    @extend_schema(
        methods=["get", "put", "delete", "post"], description="Get/Update/Delete/Add extra metadata for resource"
    )
    @action(
        detail=True,
        methods=["get", "put", "delete", "post"],
        permission_classes=[
            IsOwnerOrAdmin,
        ],
        url_path=r"extra_metadata",  # noqa
        url_name="extra-metadata",
    )
    def extra_metadata(self, request, pk=None):
        _obj = self.get_object()
        if request.method == "GET":
            # get list of available metadata
            queryset = _obj.metadata.all()
            _filters = [{f"metadata__{key}": value} for key, value in request.query_params.items()]
            if _filters:
                queryset = queryset.filter(**_filters[0])
            return Response(ExtraMetadataSerializer().to_representation(queryset))
        if not request.method == "DELETE":
            try:
                extra_metadata = validate_extra_metadata(request.data, _obj)
            except Exception as e:
                return Response(status=500, data=e.args[0])

        if request.method == "PUT":
            '''
            update specific metadata. The ID of the metadata is required to perform the update
            [
                {
                        "id": 1,
                        "name": "foo_name",
                        "slug": "foo_sug",
                        "help_text": "object",
                        "field_type": "int",
                        "value": "object",
                        "category": "object"
                }
            ]
            '''
            for _m in extra_metadata:
                _id = _m.pop('id')
                ResourceBase.objects.filter(id=_obj.id).first().metadata.filter(id=_id).update(metadata=_m)
            logger.info("metadata updated for the selected resource")
            _obj.refresh_from_db()
            return Response(ExtraMetadataSerializer().to_representation(_obj.metadata.all()))
        elif request.method == "DELETE":
            # delete single metadata
            '''
            Expect a payload with the IDs of the metadata that should be deleted. Payload be like:
            [4, 3]
            '''
            ResourceBase.objects.filter(id=_obj.id).first().metadata.filter(id__in=request.data).delete()
            _obj.refresh_from_db()
            return Response(ExtraMetadataSerializer().to_representation(_obj.metadata.all()))
        elif request.method == "POST":
            # add new metadata
            '''
            [
                {
                        "name": "foo_name",
                        "slug": "foo_sug",
                        "help_text": "object",
                        "field_type": "int",
                        "value": "object",
                        "category": "object"
                }
            ]
            '''
            for _m in extra_metadata:
                new_m = ExtraMetadata.objects.create(
                    resource=_obj,
                    metadata=_m
                )
                new_m.save()
                _obj.metadata.add(new_m)
            _obj.refresh_from_db()
            return Response(ExtraMetadataSerializer().to_representation(_obj.metadata.all()), status=201)


class ResourceVersionViewSet(DynamicModelViewSet):
    """
    API endpoint that lists all versioning resources.
    """
    authentication_classes = [SessionAuthentication, BasicAuthentication, OAuth2Authentication]
    if settings.DEFAULT_ANONYMOUS_ACCESS_PERMISSION:
        permission_classes = [AllowAny, ]
    else:
        permission_classes = [IsAuthenticated, ]

    queryset = ResourceVersion.objects.all()
    serializer_class = ResourceVersionSerializer
    pagination_class = GeoNodeApiPagination

    def paginate_queryset(self, queryset):
        if 'all' in self.request.query_params:
            return None

        return super().paginate_queryset(queryset)

    def get_queryset(self):
        """
        Filter users with at least a versions
        """
        queryset = ResourceVersion.objects.all()
        resource_id = self.request.query_params.get('d', None)
        layer = self.request.query_params.get('l', None)
        if resource_id is not None:
            queryset = queryset.filter(resource=resource_id).order_by("-id")
        if layer is not None:
            resource_layer = get_object_or_404(ResourceBase, alternate=layer)
            queryset = queryset.filter(resource=resource_layer)

        return queryset

    @extend_schema(
        methods=['post'],
        responses={200},
        description="API endpoint allowing to fill the changes of resources.")
    @action(
        detail=False,
        url_path="set_version/(?P<resource_id>\d+)?$",
        url_name="set-version",
        methods=['post'],
        parser_classes=[JSONParser, FormParser,],
        permission_classes=[
            IsAuthenticated
        ]
    )
    def set_version(self, request, resource_id):
        import re
        version = request.data.get('version')
        summary = request.data.get('summary')
        tags = request.data.get('tags')
        contributors = get_user_model().objects.get(username=request.user).id
        latest_version = ResourceVersion.objects.filter(resource_id=resource_id).order_by('-id')[0]

        data = {
            'resource': resource_id,
            'version': version,
            'summary': summary,
            'tags': tags,
            'contributors': contributors
        }
        serializer = ResourceVersionCreateSerializer(data=data)
        match = re.match(r"(\d+\.\d+(?:\.\d+)?)", version)
        if not match:
            msg = f"Please use semantic versioning syntax like: MAJOR.MINOR -- i.e.: 1.2, 1.3, 2.0"
            return Response({"message": msg}, status=status.HTTP_400_BAD_REQUEST)

        if version == str(latest_version):
            recommended_version = (float(str(latest_version)) * 10 + 1) / 10
            msg = f"Please don't use the same version as before: {str(latest_version)}. Add increment to your MAJOR or MINOR version, say {str(recommended_version)}"
            return Response({"message": msg}, status=status.HTTP_400_BAD_REQUEST)

        if serializer.is_valid():
            serializer.save()
            msg = f'Your record has been saved'
            return Response({'message': msg, 'serializer': serializer.data}, status=status.HTTP_201_CREATED)

        return Response({"message": "Something went wrong, we couldn't save your record."}, status=status.HTTP_400_BAD_REQUEST)


    @extend_schema(
        methods=['get'],
        responses={200},
        description="API endpoint allowing to fill the changes of resources.")
    @action(
        detail=False,
        url_path="get_version/(?P<resource_id>\d+)?$",
        url_name="get-version",
        methods=['get'],
        parser_classes=[JSONParser],
        permission_classes=[
            IsAuthenticated
        ]
    )
    def get_version(self, request, resource_id):
        version = ResourceVersion.objects.filter(resource_id=resource_id)
        if version:
            version = version.only('version').order_by('-id')[0]
            return Response(data={"version": str(version)}, status=200)
        else:
            return Response(data={"message": "no previous version was founded"}, status=200)


    @extend_schema(
        methods=['get'],
        responses={200},
        description="API endpoint allowing to see the detail changes of resources.")
    @action(
        detail=False,
        url_path="get_detailed_version",
        url_name="get-detailed-version",
        methods=['get'],
        parser_classes=[JSONParser],
        permission_classes=[
            IsAuthenticated
        ]
    )
    def get_detailed_version(self, request):
        dataset_id = self.request.query_params.get('d', None)
        layer_id = self.request.query_params.get('l', None)
        get_version = self.request.query_params.get('v', None)

        if dataset_id is not None:
            version = ResourceVersion.objects.filter(resource_id=dataset_id, version=get_version)
        if layer_id is not None:
            resource_layer = get_object_or_404(ResourceBase, alternate=layer_id)
            version = ResourceVersion.objects.filter(resource=resource_layer, version=get_version)

        if version:
            return Response(data={"version": ResourceVersionChangesSerializer(many=True).to_representation(version)[0]}, status=200)
        else:
            return Response(data={"message": "no previous version was founded"}, status=200)