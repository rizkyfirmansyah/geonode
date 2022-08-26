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
from zipfile import ZipFile, ZIP_DEFLATED
from drf_spectacular.utils import extend_schema
import io
from django.utils.translation import ugettext as _
from django.contrib.auth import get_user_model
from geonode.monitoring.models import EventType
from dynamic_rest.viewsets import DynamicModelViewSet
from dynamic_rest.filters import DynamicFilterBackend, DynamicSortingFilter
from geonode.base import register_event
from geonode.datasets.enumerations import DATASET_TYPE_MAP
from ...security.utils import serialize_resource_permissions, sha256file
from ...utils import doc_path, mkdtemp
from ..models import Dataset, File
from rest_framework import viewsets

from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser, IsAuthenticated, IsAuthenticatedOrReadOnly, DjangoModelPermissionsOrAnonReadOnly  # noqa
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from oauth2_provider.contrib.rest_framework import OAuth2Authentication
from rest_framework.response import Response
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from rest_framework import status
from django.http import HttpResponse
from django_downloadview.response import DownloadResponse
from django.utils.text import slugify
import os
from django.shortcuts import get_object_or_404
from django.urls import reverse

from geonode.base.api.filters import DynamicSearchFilter, ExtentFilter
from geonode.base.api.permissions import IsOwnerOrReadOnly
from geonode.base.api.pagination import GeoNodeApiPagination
from geonode.resource.manager import resource_manager
from geonode.storage.manager import storage_manager

from geonode.base.models import ResourceBase
from geonode.base.api.serializers import ResourceBaseSerializer

from .serializers import DatasetIngestFileSerializer, DatasetIngestUrlSerializer, DatasetSerializer
from .permissions import DocumentPermissionsFilter
from django.conf import settings
import logging
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
        toast_title = f"Delete File"
        try:
            file.delete()
            msg = f"Your selected file has been deleted."
            return Response(data={'message': msg}, status=status.HTTP_200_OK)

        except NotImplementedError as e:
            logger.error(e)
            messages.error(request, message=e.args[0], extra_tags=toast_title)
            return Response(data={'message': e.args[0], 'success': False}, status=405, exception=True)

        except Exception as e:
            logger.error(e)
            messages.error(request, message=e.args[0], extra_tags=toast_title)
            return Response(data={'message': e.args[0], 'success': False}, status=500, exception=True)

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
        toast_title = f"Delete Dataset"
        try:
            file = File.objects.filter(id__in=query)
            file.delete()
            msg = f"Your files has been deleted."
            return Response(data={'message': msg}, status=status.HTTP_200_OK)

        except NotImplementedError as e:
            logger.error(e)
            messages.error(request, message=e.args[0], extra_tags=toast_title)
            return Response(data={'message': e.args[0], 'success': False}, status=405, exception=True)

        except Exception as e:
            logger.error(e)
            messages.error(request, message=e.args[0], extra_tags=toast_title)
            return Response(data={'message': e.args[0], 'success': False}, status=500, exception=True)

    @extend_schema(
        methods=['get'],
        responses={200},
        description="API endpoint allowing to edit the File.")
    @action(
        detail=False,
        url_path="edit_dataset_files/(?P<dataset_id>\d+)?$",
        url_name="edit_dataset_files",
        methods=['get'],
        permission_classes=[
            IsAuthenticated, IsOwnerOrReadOnly
        ],
        parser_classes=[JSONParser, MultiPartParser]
    )
    def edit_dataset_files(self, request, dataset_id):
        resources = File.objects.filter(dataset_id__in=[dataset_id])
        serializer = DatasetSerializer(instance=resources, embed=True, many=True)

        return Response({"files": serializer.data, "length": resources.count()})


    @extend_schema(
        methods=['patch'],
        responses={200},
        description="API endpoint allowing to edit each files of Dataset.")
    @action(
        detail=False,
        url_path="patch_dataset_files/(?P<dataset_id>\d+)?$",
        url_name="patch_dataset_files",
        methods=['patch'],
        permission_classes=[
            IsAuthenticated,
        ]
    )
    def patch_dataset_files(self, request, dataset_id):
        session_uuid = request.session.get('session')
        _data = request.data.copy()
        for item in _data:
            item.update( {"session": session_uuid} )

        data = {
            int(i['id']): {k: v for k, v in i.items() if k != 'id'} for i in _data
        }
        toast_title = f"Upload Datasets"
        try:
            for inst in self.get_queryset().filter(id__in=data.keys()):
                title = inst.file_name
                serializer = self.get_serializer(inst, data=data[inst.id], partial=True)
                serializer.is_valid(raise_exception=True)
                serializer.save()

            msg = f"Your files has been saved."
            messages.success(request, msg, extra_tags=toast_title)

            return Response({"message": "Your file has been updated", "response": reverse('dataset_detail', args=(dataset_id,))}, status=status.HTTP_201_CREATED)
        
        except NotImplementedError as e:
            logger.error(e)
            messages.error(request, message=e.args[0], extra_tags=toast_title)
            return Response(data={"message:": e.args[0], 'success': False}, status=405, exception=True)

        except Exception as e:
            logger.error(e)
            messages.error(request, message=e.args[0], extra_tags=toast_title)
            return Response(data={"message:": e.args[0], 'success': False}, status=500, exception=True)

    @extend_schema(
        methods=['get'],
        responses={200},
        description="API endpoint allowing to download single file of Dataset.")
    @action(
        detail=False,
        url_path="download_dataset_file/(?P<pk>\d+)?$",
        url_name="download_dataset_file",
        methods=['get'],
        permission_classes=[
            IsAuthenticated,
        ]
    )
    def download_dataset_file(self, request, pk):
        file = File.objects.filter(id=pk).get()
        filename = file.file_name.split(".")[0]
        try:
            if file.file and storage_manager.exists(file.file):
                return DownloadResponse(
                    storage_manager.open(file.file),
                    basename=f'{filename}.{file.extension}'
                )
        except Exception as e:
            logger.error(e)

        return HttpResponse(
            "File is not available",
            status=404
        )


    @extend_schema(
        methods=['post', 'get'],
        responses={200},
        description="API endpoint allowing to download all files of Dataset.")
    @action(
        detail=False,
        url_path="download_dataset_files/(?P<dataset_id>\d+)?$",
        url_name="download_dataset_files",
        methods=['post', 'get'],
        permission_classes=[
            IsAuthenticated,
        ]
    )
    def download_dataset_files(self, request, dataset_id):
        import requests
        import mimetypes
        import gdown
        import shutil
        resources = File.objects.filter(dataset__id__in=[dataset_id])
        dataset = Dataset.objects.filter(resourcebase_ptr=dataset_id).first()
        toast_title = f"Download Dataset Files"
        output = io.BytesIO()
        zf = ZipFile(output, 'w', ZIP_DEFLATED)
        def download_file_from_google_drive(url, filename, tempdir):
            try:
                gfile = gdown.download(url=url, output=tempdir, fuzzy=True)
            except Exception as e:
                logger.error(e)
            finally:
                zf.write(gfile, arcname=filename)
        try:
            try:
                for file in resources:
                    if file.file:
                        fdir, fname = os.path.split(file.file)
                        zf.write(file.file, arcname=fname)
                    elif file.file_url:
                        tempdir = mkdtemp()
                        response = requests.get(file.file_url, stream=True)
                        if "drive.google" in file.file_url:
                            download_file_from_google_drive(file.file_url, file.file_name, os.path.join(tempdir, file.file_name))
                        elif "sharepoint.com" in file.file_url:
                            messages.error(request, message=f"Apologies we couldn't download the file from sharepoint right now. Please find the external file below and download manually.", extra_tags=toast_title)
                        else:
                            content_type = response.headers['content-type']
                            extension = mimetypes.guess_extension(content_type)
                            if response.status_code != requests.codes.ok:
                                return HttpResponse("File is not available", status=404)

                            if extension:
                                zf.writestr(f'{file.file_name}{extension}', response.content)
                            else:
                                zf.writestr(f'{file.file_name}', response.content)

            except FileNotFoundError:
                logger.error(f"Try to download dataset files but not found")

            finally:
                zf.close()
                shutil.rmtree(tempdir, ignore_errors=True)

            return HttpResponse(output.getvalue(), content_type='application/zip', headers={'Content-Disposition': 'attachment; filename='f"{dataset}.zip"''})

        except NotImplementedError as e:
            logger.error(e)
            messages.error(request, message=e.args[0], extra_tags=toast_title)
            return Response(data={"message:": e.args[0], 'success': False}, status=405, exception=True)

        except Exception as e:
            logger.error(e)
            messages.error(request, message=e.args[0], extra_tags=toast_title)
            return Response(data={"message:": e.args[0], 'success': False}, status=500, exception=True)


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
    def resume_upload(self, request):
        resources = File.objects.filter(dataset_id__isnull=True, owner=get_user_model().objects.get(username=request.user).id)
        serializer = DatasetSerializer(instance=resources, embed=True, many=True)
        files_length = resources.count()

        if (files_length > 0):
            toast_title = f"Resume Upload"
            msg = f"You have unresolved files to upload."
            messages.warning(request, msg, extra_tags=toast_title)

        return Response({"files": serializer.data, "length": files_length})

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
        ],
        parser_classes=[JSONParser, MultiPartParser]
    )
    def upload_dataset_files(self, request):
        import json
        # ref https://stackoverflow.com/questions/53130126/bulk-partial-updates-with-django-rest-framework
        session_uuid = request.session.get('session')
        _data = request.data.copy()
        for item in _data:
            permissions = item['permissions']
            del item['permissions']
            item.update( {"session": session_uuid} )

        data = {
            int(i['id']): {k: v for k, v in i.items() if k != 'id'} for i in _data
        }

        toast_title = f"Upload Datasets"
        resource_permissions = serialize_resource_permissions(json.loads(permissions))

        try:
            for inst in self.get_queryset().filter(id__in=data.keys()):
                title = inst.file_name
                serializer = self.get_serializer(inst, data=data[inst.id], partial=True)
                serializer.is_valid(raise_exception=True)
                serializer.save()
            self.object = resource_manager.create(
                None,
                resource_type=Dataset,
                defaults=dict(
                    owner=self.request.user,
                    title=title,
                    resource_type='dataset'
                )
            )
            self.object.handle_moderated_uploads()
            resource_manager.set_permissions(
                None, instance=self.object, permissions=resource_permissions, created=True
            )
            update_file = File.objects.filter(dataset_id__isnull=True).update(dataset=self.object.id)
            update_detail_url = ResourceBase.objects.filter(id=self.object.id).update(detail_url='/datasets/'+str(self.object.id))
            register_event(self.request, EventType.EVENT_UPLOAD, self.object)

            msg = f"Your files has been saved."
            messages.success(request, msg, extra_tags=toast_title)

            return Response({"message": "Your file has been updated", "response": reverse('dataset_metadata', args=(self.object.id,))}, status=status.HTTP_201_CREATED)

        except NotImplementedError as e:
            logger.error(e)
            messages.error(request, message=e.args[0], extra_tags=toast_title)
            return Response(data={'message': e.args[0], 'success': False}, status=405, exception=True)

        except Exception as e:
            logger.error(e)
            messages.error(request, message=e.args[0], extra_tags=toast_title)
            return Response(data={"message": e.args[0], "success": False}, status=500, exception=True)


class DatasetIngestView(viewsets.ModelViewSet):
    """
    Retrieve, update or delete a Dataset File instance
    """    
    parser_classes = [MultiPartParser, JSONParser,]
    serializer_class = DatasetIngestFileSerializer

    def post(self, request, *args, **kwargs):
        file_url = request.POST['file_url']
        import_id = request.POST['import_id']
        try:
            dataset_id = request.POST['dataset_id']
        except Exception:
            dataset_id = None

        if not file_url:
            ext = request.POST['extension']
            file_name = request.POST['file_name']
            file = request.FILES['file']
            file_size = request.POST['file_size']
            file_type = [v for k, v in DATASET_TYPE_MAP.items() if ext in k.lower()]
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
                'session': request.session.get('session'),
                'dataset': dataset_id,
                'owner': get_user_model().objects.get(username=request.user).id
            }
            serializer = DatasetIngestFileSerializer(data=data)
        else:
            data = {
                'file_url': file_url,
                'import_id': import_id,
                'session': request.session.get('session'),
                'dataset': dataset_id,
                'owner': get_user_model().objects.get(username=request.user).id
            }
            serializer = DatasetIngestUrlSerializer(data=data)
        
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Adding new dataset file", "files": serializer.data}, status=status.HTTP_201_CREATED)
        
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
        resources = get_object_or_404(File, pk=pk)
        filename = slugify(os.path.splitext(os.path.basename(resources.file_name))[0])
        import numpy as np
        import pandas as pd
        try:
            if resources.file_type == 'tabular':
                def replace_nan(df):
                    # replace all NaNs with an empty string
                    df = df.replace(np.nan, '', regex=True)
                    return df

                if resources.extension == 'csv':
                    df = pd.read_csv(resources.file)
                    df = df.head(200)
                    replace_nan(df)

                elif resources.extension == 'tsv':
                    df = pd.read_csv(resources.file, sep='\t', header=0)
                    df = df.head(200)
                    replace_nan(df)
                
                elif resources.extension == 'sav':
                    df = pd.read_spss(resources.file)
                    df = df.head(200)
                    replace_nan(df)

                classes = 'table table-sm'
                render_df = df.to_html(classes=classes, justify='center', table_id='tabular_data')
                
                return HttpResponse(render_df)

            if resources.file_type == 'text':
                return HttpResponse(storage_manager.open(resources.file), content_type="text/plain")

            elif resources.file and storage_manager.exists(resources.file):
                return DownloadResponse(
                    storage_manager.open(resources.file),
                    basename=f'{filename}.{resources.extension}'
                )
        except Exception as e:
            logger.error(e)
            
        return HttpResponse("File is not available", status=404)
