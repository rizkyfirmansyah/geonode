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
from functools import partial
from drf_spectacular.utils import extend_schema

from dynamic_rest.viewsets import DynamicModelViewSet
from dynamic_rest.filters import DynamicFilterBackend, DynamicSortingFilter
from geonode.datasets.enumerations import DOCUMENT_TYPE_MAP
from ...security.utils import sha256file
from ...utils import doc_path
from ..models import Dataset, File
from rest_framework import viewsets

from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser, IsAuthenticated, IsAuthenticatedOrReadOnly, DjangoModelPermissionsOrAnonReadOnly  # noqa
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from oauth2_provider.contrib.rest_framework import OAuth2Authentication
from rest_framework.response import Response
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from rest_framework.exceptions import ValidationError
from rest_framework import status
from django.db.models import Max

from django.shortcuts import get_object_or_404
from django.urls import reverse

from geonode.base.api.filters import DynamicSearchFilter, ExtentFilter
from geonode.base.api.permissions import IsOwnerOrReadOnly
from geonode.base.api.pagination import GeoNodeApiPagination
from geonode.resource.manager import resource_manager
from geonode.storage.manager import storage_manager

from geonode.base.models import ResourceBase
from geonode.base.api.serializers import ResourceBaseSerializer
from rest_framework.views import APIView

from .serializers import DatasetIngestFileSerializer, DatasetIngestUrlSerializer, DatasetSerializer
from .permissions import DocumentPermissionsFilter
from django.conf import settings
import logging
from django.http import HttpResponseRedirect
from django.contrib import messages

logger = logging.getLogger(__name__)


class DatasetsViewSet(DynamicModelViewSet):
    """
    API endpoint that allows datasets to be viewed or edited.
    """
    http_method_names = ['get', 'patch', 'put', 'delete']
    authentication_classes = [SessionAuthentication, BasicAuthentication, OAuth2Authentication]
    if settings.DEFAULT_ANONYMOUS_ACCESS_PERMISSION:
        permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    else:
        permission_classes = [IsAuthenticated, ]
    filter_backends = [
        DynamicFilterBackend, DynamicSortingFilter, DynamicSearchFilter,
        ExtentFilter, DocumentPermissionsFilter
    ]
    queryset = File.objects.all().order_by('-last_updated')
    serializer_class = DatasetSerializer
    pagination_class = GeoNodeApiPagination

    @extend_schema(methods=['get'], responses={200: ResourceBaseSerializer(many=True)},
                   description="API endpoint allowing to retrieve the FileResourceLink(s).")
    @action(detail=True, methods=['get'])
    def linked_resources(self, request, pk=None):
        document = self.get_object()
        resources_id = document.links.all().values('object_id')
        resources = ResourceBase.objects.filter(id__in=resources_id)
        exclude = []
        for resource in resources:
            if not request.user.is_superuser and \
            not request.user.has_perm('view_resourcebase', resource.get_self_resource()):
                exclude.append(resource.id)
        resources = resources.exclude(id__in=exclude)
        paginator = GeoNodeApiPagination()
        paginator.page_size = request.GET.get('page_size', 10)
        result_page = paginator.paginate_queryset(resources, request)
        serializer = ResourceBaseSerializer(result_page, embed=True, many=True)
        return paginator.get_paginated_response({"resources": serializer.data})

    @extend_schema(
        methods=['delete'],
        responses={200},
        description="API endpoint allowing to delete single file of the File.")
    @action(
        detail=False,
        url_path="delete_file",
        url_name="delete_file",
        methods=['delete'],
        permission_classes=[
            IsAuthenticated,
        ],
        parser_classes=[JSONParser, FormParser]
    )
    def delete_file(self, request):
        pk = request.data.get('pk')
        file = get_object_or_404(File, pk=pk)
        file.delete()

        return Response(status=status.HTTP_200_OK)

    @extend_schema(
        methods=['delete'],
        responses={200},
        description="API endpoint allowing to delete relevant files of the File.")
    @action(
        detail=False,
        url_path="delete_files",
        url_name="delete_files",
        methods=['delete'],
        permission_classes=[
            IsAuthenticated,
        ],
        parser_classes=[JSONParser, FormParser]
    )
    def delete_files(self, request):
        query = request.data.getlist('ids[]')

        file = File.objects.filter(id__in=query)
        file.delete()

        return Response(status=status.HTTP_200_OK)

    @extend_schema(
        methods=['get'],
        responses={200},
        description="API endpoint for preview file.")
    @action(
        detail=False,
        methods=['get'],
        permission_classes=[
            IsAuthenticated,
        ],
        parser_classes=[JSONParser, MultiPartParser]
    )
    def preview_file(self, request, pk):
        from django.template import loader
        from django.http import HttpResponse
        from django_downloadview.response import DownloadResponse
        from django.utils.text import slugify
        import os

        resources = get_object_or_404(File, pk=pk)
        if not request.user.has_perm(
            'base.download_resourcebase',
            obj=resources.get_self_resource()):
            return HttpResponse(
                loader.render_to_string(
                    'error/401.html', context={
                        'error_message': _("You are not allowed to view this dataset.")}, request=request), status=401)
        filename = slugify(os.path.splitext(os.path.basename(resources.title))[0])

        if resources.file and storage_manager.exists(resources.file[0]):
            return DownloadResponse(
                storage_manager.open(resources.file[0]).file,
                basename=f'{filename}.{resources.extension}'
            )

        return HttpResponse(
            "File is not available",
            status=404
        )

    @extend_schema(
        methods=['get'],
        responses={200},
        description="API endpoint allowing to resume the upload files of the File.")
    @action(
        detail=False,
        url_path="resume_upload",
        url_name="resume_upload",
        methods=['get'],
        permission_classes=[
            IsAuthenticated,
        ],
        parser_classes=[JSONParser, MultiPartParser]
    )
    def get(self, request):

        resources = File.objects.filter(dataset_id__isnull=True)
        exclude = []
        for resource in resources:
            if not request.user.is_superuser and \
            not request.user.has_perm('view_file', resource.get_self_resource()):
                exclude.append(resource.id)
        resources = resources.exclude(id__in=exclude)
        serializer = DatasetSerializer(instance=resources, embed=True, many=True)

        return Response({"files": serializer.data, "length": resources.count()})

    @extend_schema(
        methods=['patch'],
        responses={200},
        description="API endpoint allowing to save the upload files of the File.")
    @action(
        detail=False,
        url_path="upload_dataset_files",
        url_name="upload_dataset_files",
        methods=['patch'],
        permission_classes=[
            IsAuthenticated,
        ]
    )
    def patch(self, request):
        # ref https://stackoverflow.com/questions/53130126/bulk-partial-updates-with-django-rest-framework
        session_uuid = request.session.get('session')
        _data = request.data.copy()
        for item in _data:
            item.update( {"session": session_uuid} )

        data = {
            int(i['id']): {k: v for k, v in i.items() if k != 'id'} for i in _data
        }
        for inst in self.get_queryset().filter(id__in=data.keys()):
            title = inst.file_name
            serializer = self.get_serializer(inst, data=data[inst.id], partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()

        toast_title = f"Upload Datasets"
        msg = f"Your files has been saved."
        messages.success(request, msg, extra_tags=toast_title)

        self.object = resource_manager.create(
            None,
            resource_type=Dataset,
            defaults=dict(
                owner=self.request.user,
                title=title,
                resource_type='dataset'
            )
        )
        update_file = File.objects.filter(dataset_id__isnull=True).update(dataset=self.object.id)

        return Response({"message": "Your file has been updated", "response": reverse('dataset_metadata', args=(self.object.id,))}, status=status.HTTP_201_CREATED)

class DatasetIngestView(viewsets.ModelViewSet):
    """
    Retrieve, update or delete a Dataset File instance
    """
    parser_classes = [MultiPartParser, JSONParser,]
    serializer_class = DatasetIngestFileSerializer

    def post(self, request, *args, **kwargs):
        file_url = request.POST['file_url']
        import_id = request.POST['import_id']

        if not file_url:
            ext = request.POST['extension']
            file_name = request.POST['file_name']
            file = request.FILES['file']
            file_size = request.POST['file_size']
            file_type = [v for k, v in DOCUMENT_TYPE_MAP.items() if ext in k.lower()]
            dirname = doc_path(ext)
            filepath = storage_manager.save(f"{dirname}/{file_name}", file)
            storage_path = storage_manager.path(filepath)
            
            data = {
                'file_name': file_name,
                'file': storage_path,
                'file_size': file_size,
                'hash': sha256file(storage_path),
                'extension': ext,
                'file_type': file_type[0],
                'import_id': import_id,
                'session': request.session.get('session')
            }
            serializer = DatasetIngestFileSerializer(data=data)
        else:
            data = {
                'file_url': file_url,
                'import_id': import_id,
                'session': request.session.get('session')
            }
            serializer = DatasetIngestUrlSerializer(data=data)
        
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Adding new dataset file", "files": serializer.data}, status=status.HTTP_201_CREATED)
        else:
            if storage_path:
                storage_manager.delete(storage_path)
            return Response({"message": serializer.errors, "files": None}, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        methods=['get'],
        responses={200},
        description="API endpoint for preview file.")
    @action(
        detail=False,
        methods=['get'],
        permission_classes=[
            IsAuthenticated,
        ],
        parser_classes=[JSONParser, MultiPartParser]
    )
    def preview_file(self, request, pk):
        from django.http import HttpResponse
        from django_downloadview.response import DownloadResponse
        from django.utils.text import slugify
        import os
        resources = get_object_or_404(File, pk=pk)
        filename = slugify(os.path.splitext(os.path.basename(resources.file_name))[0])

        if resources.file and storage_manager.exists(resources.file):
            return DownloadResponse(
                storage_manager.open(resources.file),
                basename=f'{filename}.{resources.extension}'
            )

        return HttpResponse(
            "File is not available",
            status=404
        )


class DatasetIngestDetailView(APIView):
    """
    Retrieve, update or delete a Dataset File instance
    """
    # renderer_classes = [TemplateHTMLRenderer]
    # template_name = 'dataset_ingest.html'
    parser_classes = [MultiPartParser, JSONParser,]

    def put(self, request, filename, format=None):
        file_obj = request.data['file']
        # ...
        # do some stuff with uploaded file
        # ...
        return Response(status=204)

