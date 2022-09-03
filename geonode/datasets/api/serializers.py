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
from collections import OrderedDict
from rest_framework import serializers
from dynamic_rest.serializers import DynamicModelSerializer

import logging

from ..models import File

logger = logging.getLogger(__name__)


class DatasetSerializer(DynamicModelSerializer):

    def __init__(self, *args, **kwargs):
        # Instantiate the superclass normally
        super().__init__(*args, **kwargs)
        self.fields['id'] = serializers.CharField(read_only=True)
        self.fields['file_name'] = serializers.CharField()
        self.fields['file_description'] = serializers.CharField(required=False, allow_blank=True)
        self.fields['file_data_quality'] = serializers.CharField(required=False, allow_blank=True)
        self.fields['file_url'] = serializers.CharField(required=False, allow_blank=True)
        self.fields['hash'] = serializers.CharField(read_only=True)
        self.fields['extension'] = serializers.CharField(read_only=True)
        self.fields['file_type'] = serializers.CharField(read_only=True)
        self.fields['created'] = serializers.DateTimeField(read_only=True)
        self.fields['last_updated'] = serializers.DateTimeField(read_only=True)
        self.fields['session'] = serializers.CharField(required=True)
        self.fields['dataset'] = serializers.CharField(read_only=True)

    class Meta:
        model = File
        name = 'datasets'
        view_name = 'datasets-file'
        fields = (
            'pk', 'id', 'file_name', 'file_description', 'file_data_quality', 'file',
            'file_url', 'hash', 'created', 'file_size', 'session', 'extension', 'file_type', 'dataset'
        )
        read_only_fileds = ('id', 'hash', 'file_size', 'created', 'extension', 'file_type', 'dataset')


class DatasetIngestFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = File
        fields = ["id", "file_name", "file", "file_size", "hash", "extension", "import_id", "session", "file_type", "dataset", "owner"]


class DatasetIngestUrlSerializer(serializers.ModelSerializer):
    class Meta:
        model = File
        fields = ["id", "file_url", "import_id", "session", "dataset", "owner", 'extension']