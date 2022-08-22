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

"""Utilities for managing GeoNode documents
"""

# Standard Modules
import os
import logging
from geonode.storage.manager import storage_manager
# Django functionality
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.template import loader
from django.utils.translation import ugettext as _
from django.utils.text import slugify
from django_downloadview.response import DownloadResponse

# Geonode functionality
from geonode.datasets.models import File
from geonode.base import register_event
from geonode.monitoring.models import EventType
from django.conf import settings

logger = logging.getLogger(__name__)


def get_download_response(request, docid, attachment=False):
    """
    Returns a download response if user has access to download the dataset of a given id,
    and an http response if they have no permissions to download it.
    """
    dataset = get_object_or_404(File, pk=docid)

    if not request.user.has_perm(
            'base.download_resourcebase',
            obj=dataset.get_self_resource()):
        return HttpResponse(
            loader.render_to_string(
                'error/401.html', context={
                    'error_message': _("You are not allowed to view this dataset.")}, request=request), status=401)
    if attachment:
        register_event(request, EventType.EVENT_DOWNLOAD, dataset)
    filename = slugify(os.path.splitext(os.path.basename(dataset.file_name))[0])

    if dataset.file and storage_manager.exists(dataset.file):
        return DownloadResponse(
            storage_manager.open(dataset.file),
            basename=f'{filename}.{dataset.extension}',
            attachment=attachment
        )
    return HttpResponse(
        "File is not available",
        status=404
    )


def document_path(filename):
    return os.path.join(settings.DOCUMENT_LOCATION, filename)