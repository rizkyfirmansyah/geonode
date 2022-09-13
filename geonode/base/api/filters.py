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
from geonode.datasets.models import File
from geonode.favorite.models import Favorite
import logging
from geonode.security.utils import get_resources_with_perms
from rest_framework.filters import SearchFilter, BaseFilterBackend
from geonode.base.bbox_utils import filter_bbox
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)


class DynamicSearchFilter(SearchFilter):

    def get_search_fields(self, view, request):
        return request.GET.getlist('search_fields', [])


class ExtentFilter(BaseFilterBackend):
    """
    Filter that only allows users to see their own objects.
    """

    def filter_queryset(self, request, queryset, view):
        if request.query_params.get('extent'):
            return filter_bbox(queryset, request.query_params.get('extent'))
        return queryset


class ResourceBaseFilter(BaseFilterBackend):
    """
    Filter that only allows users to see their own objects.
    """
    def filter_queryset(self, request, queryset, _):
        queryset = get_resources_with_perms(request.user).order_by('-date')
        order_by = request.query_params.get('order_by', None)
        search_input = request.query_params.get('dbbc87e', None)
        date_gte = request.query_params.get('date__gte', None)
        date_range = request.query_params.get('date__range', None)
        date_lte = request.query_params.get('date__lte', None)
        regions = request.query_params.get('90ca628', None)
        featured = request.query_params.get("d5da2e3", None)
        favorited = request.query_params.get("fcb5b87", None)
        resource_type = request.GET.getlist('9fadb94')
        data_type = request.GET.getlist('182243e')
        category = request.GET.getlist('f4e493d')
        tkeywords = request.GET.getlist('ebe16ff')
        keywords = request.GET.getlist('7e31fcb')
        extension = request.GET.getlist('36db053')
        group = request.GET.getlist('5af2a45')
        owner = request.GET.getlist('225d70a')

        if owner:
            queryset = queryset.filter(owner__username__in=owner)

        if search_input:
            queryset = queryset.filter(
                Q(title__icontains=search_input) |
                Q(abstract__icontains=search_input) |
                Q(data_quality_statement__icontains=search_input) |
                Q(purpose__icontains=search_input) |
                Q(data_description__icontains=search_input)
            )
        if order_by:
            queryset = queryset.order_by(order_by)

        if date_gte:
            queryset = queryset.filter(date__gte=date_gte)
        elif date_lte:
            queryset = queryset.filter(date__lte=date_lte)
        elif date_range:
            date_range = date_range.split(",")
            queryset = queryset.filter(date__range=date_range)

        if resource_type:
            queryset = queryset.filter(resource_type__in=resource_type)

        if data_type:
            queryset = queryset.filter(data_type__identifier__in=data_type)

        if category:
            queryset = queryset.filter(category__identifier__in=category)

        if tkeywords:
            queryset = queryset.filter(tkeywords__id__in=tkeywords)

        if keywords:
            queryset = queryset.filter(keywords__slug__in=keywords)

        if extension:
            file = File.objects.filter(extension__in=extension).values('dataset_id')
            queryset = queryset.filter(id__in=file)

        if regions:
            queryset = queryset.filter(regions__name=regions)

        if group:
            queryset = queryset.filter(group_id__in=group)

        if featured:
            if featured == 'true':
                queryset = queryset.filter(featured=True)
            else:
                queryset = queryset.filter(featured=False)

        try:
            _user = get_user_model().objects.get(username=request.user)
            if not str(_user) == 'AnonymousUser':
                is_favorited = Favorite.objects.favorites_for_user(user=_user).values('object_id')
        except ObjectDoesNotExist:
            pass

        if favorited:
            if favorited == 'true':
                queryset = queryset.filter(id__in=is_favorited)
            else:
                queryset = queryset.exclude(id__in=is_favorited)

        return queryset.distinct()
