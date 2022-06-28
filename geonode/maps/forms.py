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

from geonode.base.forms import ResourceBaseForm
from geonode.base.models import ResourceBase
from geonode.documents.forms import GroupsChoiceField
from geonode.maps.models import Map
from django.contrib.auth.models import Group


class MapForm(ResourceBaseForm):
    group = GroupsChoiceField(
        queryset = Group.objects.exclude(groupprofile=None),
        required=False)

    class Meta(ResourceBaseForm.Meta):
        model = Map
        exclude = ResourceBaseForm.Meta.exclude + (
            'zoom',
            'projection',
            'center_x',
            'center_y',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            help_text = self.fields[field].help_text
            self.fields[field].help_text = None
            if help_text != '':
                self.fields[field].widget.attrs.update({
                    'class': 'has-external-popover text-truncate',
                    'data-content': help_text,
                    'placeholder': help_text,
                    'data-placement': 'right',
                    'data-container': 'body',
                    'data-html': 'true',
                    'data-field': self.fields[field].label})

            if self.fields[field].widget.__class__.__name__ != 'ResourceBaseDateTimePicker':
                self.fields[field].widget.attrs.update({
                  'class': 'has-external-popover text-truncate w-100'})

            if field == 'owner':
                self.fields[field].widget.attrs.update({
                  'class': 'has-external-popover selectpicker form-control',
                  'data-live-search': 'true',
                  'data-size': '5'})
            if field == 'poc':
                self.fields[field].widget.attrs.update({
                  'class': 'has-external-popover selectpicker form-control',
                  'data-live-search': 'true',
                  'data-width': '100%',
                  'data-size': '5'})
            if field == 'metadata_author':
                self.fields[field].widget.attrs.update({
                  'class': 'has-external-popover selectpicker form-control',
                  'data-live-search': 'true',
                  'data-size': '5'})
            if field == 'group':
                self.fields[field].widget.attrs.update({
                  'class': 'has-external-popover selectpicker form-control',
                  'data-live-search': 'true',
                  'data-size': '5'})

            if field == 'regions':
                self.fields[field].help_text = ResourceBase.regions_help_text
                self.fields[field].widget.attrs.update({
                  'class': 'has-external-popover selectpicker',
                  'data-live-search': 'true',
                  'data-selected-text-format': 'count > 4',
                  'data-size': '10'})

    class Meta(ResourceBaseForm.Meta):
        model = Map
        exclude = ResourceBaseForm.Meta.exclude + (
            'zoom',
            'projection',
            'center_x',
            'center_y',
            'doi'
        )
        fields = [
          'title',
          'abstract',
          'keywords',
          'data_description',
          'purpose',
          'supplemental_information',
          'data_quality_statement',
          'author',
          'source',
          'license',
          'data_type',
          'constraints_other',
          'restriction_code_type',
          'language',
          'regions',
          'date',
          'date_type',
          'date_distribution',
          'edition',
          'maintenance_frequency',
          'temporal_extent_start',
          'temporal_extent_end',
          'spatial_representation_type',
          'spatial_resolution',
          'poc',
          'owner',
          'contacts',
          'group',
          'metadata_uploaded_preserve',
          'featured',
          'metadata_only',
          'was_published',
          'is_published',
          'was_approved',
          'is_approved',
          'thumbnail_url',
          'metadata'
        ]
