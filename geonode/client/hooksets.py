#########################################################################
#
# Copyright (C) 2018 OSGeo
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
import json

def resource_list_url(resource_type):
    return '/{}/upload'.format(resource_type)

def resource_detail_url(resource_type, resource_id):
    return '/catalogue/#/{}/{}'.format(resource_type, resource_id)


class BaseHookSet:

    # Layers
    def layer_list_template(self, context=None):
        return 'layers/layer_list_default.html'

    def layer_detail_template(self, context=None):
        return NotImplemented

    def layer_new_template(self, context=None):
        return NotImplemented

    def layer_view_template(self, context=None):
        return NotImplemented

    def layer_edit_template(self, context=None):
        return NotImplemented

    def layer_update_template(self, context=None):
        return NotImplemented

    def layer_embed_template(self, context=None):
        return NotImplemented

    def layer_download_template(self, context=None):
        return NotImplemented

    def layer_style_edit_template(self, context=None):
        return NotImplemented

    def layer_list_url(self):
        return resource_list_url('layers')

    def layer_upload_url(self):
        return '/catalogue/#/upload/layer'

    def layer_detail_url(self, resource):
        return resource_detail_url('layer', resource.id)

    # Maps
    def map_list_template(self, context=None):
        return 'maps/map_list_default.html'

    def map_detail_template(self, context=None):
        return NotImplemented

    def map_new_template(self, context=None):
        return NotImplemented

    def map_view_template(self, context=None):
        return NotImplemented

    def map_edit_template(self, context=None):
        return NotImplemented

    def map_update_template(self, context=None):
        return NotImplemented

    def map_embed_template(self, context=None):
        return NotImplemented

    def map_download_template(self, context=None):
        return NotImplemented

    def map_list_url(self, resource):
        return resource_list_url('map')

    def map_detail_url(self, resource):
        return resource_detail_url('map', resource.id)

    # GeoApps
    def geoapp_list_template(self, context=None):
        return 'apps/app_list_default.html'

    def geoapp_detail_template(self, context=None):
        return NotImplemented

    def geoapp_new_template(self, context=None):
        return NotImplemented

    def geoapp_view_template(self, context=None):
        return NotImplemented

    def geoapp_edit_template(self, context=None):
        return NotImplemented

    def geoapp_update_template(self, context=None):
        return NotImplemented

    def geoapp_embed_template(self, context=None):
        return NotImplemented

    def geoapp_download_template(self, context=None):
        return NotImplemented

    # def geoapp_list_url(self):
    #     return resource_list_url('geostory')

    # def geoapp_detail_url(self, resource):
    #     return resource_detail_url(resource.resource_type, resource.id)

    # Documents
    def document_list_url(self):
        return resource_list_url('documents')

    def document_detail_url(self, resource):
        return resource_detail_url('documents', resource.id)

    # Map Persisting
    def viewer_json(self, conf, context=None):
        if isinstance(conf, str):
            conf = json.loads(conf)
        return conf

    def update_from_viewer(self, conf, context=None):
        conf = self.viewer_json(conf, context=context)
        context['config'] = conf
        return 'maps/map_edit.html'


class LeafletHookSet(BaseHookSet):

    # Layers
    def layer_detail_template(self, context=None):
        return 'leaflet/layers/layer_leaflet_map.html'

    def layer_new_template(self, context=None):
        return 'leaflet/layers/layer_leaflet_map.html'

    def layer_view_template(self, context=None):
        return 'leaflet/layers/layer_leaflet_map.html'

    def layer_edit_template(self, context=None):
        return 'leaflet/layers/layer_leaflet_map.html'

    def layer_update_template(self, context=None):
        return 'leaflet/layers/layer_leaflet_map.html'

    def layer_embed_template(self, context=None):
        return 'leaflet/layers/layer_leaflet_map.html'

    def layer_download_template(self, context=None):
        return 'leaflet/layers/layer_leaflet_map.html'

    def layer_style_edit_template(self, context=None):
        return 'leaflet/layers/layer_leaflet_map.html'

    # Maps
    def map_detail_template(self, context=None):
        return 'leaflet/maps/map_view.html'

    def map_new_template(self, context=None):
        return 'leaflet/maps/map_view.html'

    def map_view_template(self, context=None):
        return 'leaflet/maps/map_view.html'

    def map_edit_template(self, context=None):
        return 'leaflet/maps/map_edit.html'

    def map_update_template(self, context=None):
        return 'leaflet/maps/map_edit.html'

    def map_embed_template(self, context=None):
        return 'leaflet/maps/map_detail.html'

    def map_download_template(self, context=None):
        return 'leaflet/maps/map_embed.html'


class ReactHookSet(BaseHookSet):

    # Layers
    def layer_detail_template(self, context=None):
        return 'geonode-client/layer_map.html'

    def layer_new_template(self, context=None):
        return 'geonode-client/layer_map.html'

    def layer_view_template(self, context=None):
        return 'geonode-client/layer_map.html'

    def layer_edit_template(self, context=None):
        return 'geonode-client/layer_map.html'

    def layer_update_template(self, context=None):
        return 'geonode-client/layer_map.html'

    def layer_embed_template(self, context=None):
        return 'geonode-client/layer_map.html'

    def layer_download_template(self, context=None):
        return 'geonode-client/layer_map.html'

    def layer_style_edit_template(self, context=None):
        return 'geonode-client/layer_map.html'

    # Maps
    def map_detail_template(self, context=None):
        return 'geonode-client/map_detail.html'

    def map_new_template(self, context=None):
        return 'geonode-client/map_new.html'

    def map_view_template(self, context=None):
        return 'geonode-client/map_view.html'

    def map_edit_template(self, context=None):
        return 'geonode-client/edit_map.html'

    def map_update_template(self, context=None):
        return 'geonode-client/edit_map.html'

    def map_embed_template(self, context=None):
        return 'geonode-client/map_view.html'

    def map_download_template(self, context=None):
        return 'geonode-client/map_view.html'
