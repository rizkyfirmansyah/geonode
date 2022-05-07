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
from geonode.geoapps.models import GeoApp
from geonode.base.forms import ResourceBaseForm


class GeoAppForm(ResourceBaseForm):

    class Meta(ResourceBaseForm.Meta):
        model = GeoApp
        exclude = ResourceBaseForm.Meta.exclude + (
            'zoom',
            'projection',
            'center_x',
            'center_y',
            'data'
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
          'doi',
          'license',
          'data_type',
          'constraints_other',
          'restriction_code_type',
          'language',
          'regions',
          'date',
          'date_content',
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
          'was_published',
          'is_published',
          'was_approved',
          'is_approved',
          'thumbnail_url',
          'metadata',
          'metadata_only'
        ]

    def __init__(self, *args, **kwargs):
        super(GeoAppForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            help_text = self.fields[field].help_text
            self.fields[field].help_text = None
            if help_text != '':
                self.fields[field].widget.attrs.update(
                    {
                        'class': 'has-external-popover',
                        'data-content': help_text,
                        'placeholder': help_text,
                        'data-placement': 'right',
                        'data-container': 'body',
                        'data-html': 'true'
                    }
                )
