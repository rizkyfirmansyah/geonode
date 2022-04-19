# -*- coding: utf-8 -*-
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
import copy
import json
import logging
import collections
from itertools import chain

import requests
import traceback
from lxml import etree
import xml.etree.ElementTree as ET
from defusedxml import lxml as dlxml

from requests.auth import HTTPBasicAuth

from django.apps import apps
from django.conf import settings
from django.db.models import Q
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import Group, Permission
from django.core.exceptions import ObjectDoesNotExist
from guardian.utils import get_user_obj_perms_model
from guardian.shortcuts import (
    assign_perm,
    get_anonymous_user,
    get_objects_for_user)

from geonode import geoserver
from geonode.utils import get_layer_workspace
from geonode.decorators import on_ogc_backend
from geonode.groups.models import GroupProfile
from geonode.security.permissions import (
    PermSpecCompact,
    VIEW_PERMISSIONS,
    ADMIN_PERMISSIONS,
    SERVICE_PERMISSIONS,
    DOWNLOAD_PERMISSIONS,
    DOWNLOADABLE_RESOURCES,
    LAYER_ADMIN_PERMISSIONS,
    LAYER_EDIT_DATA_PERMISSIONS,
    LAYER_EDIT_STYLE_PERMISSIONS,
    DATA_EDITABLE_RESOURCES_SUBTYPES,
    DATA_STYLABLE_RESOURCES_SUBTYPES)
from rest_framework import exceptions

logger = logging.getLogger("geonode.security.utils")


class GeofenceRequestError(exceptions.APIException):
    pass


class GeofenceLayerAdapter(object):
    def __init__(self, resource):
        self.resource = resource
        self.__has_committed_changes = False
        self.safe_point_rules = []

    @property
    def has_committed_changes(self):
        return self.__has_committed_changes

    def set_has_committed_changes(self):
        """
        Create save point before first commit
        """
        if not self.__has_committed_changes:
            self.__has_committed_changes = True
            self.safe_point_rules = self.list_rules(xml=True)

    def purge_rules(self):
        self.set_has_committed_changes()
        purge_geofence_layer_rules(self.resource)

    def list_rules(self, xml=False):
        layer = self.resource.layer
        workspace = get_layer_workspace(layer)
        layer_name = (
            layer.name
            if layer and hasattr(layer, 'name') else
            layer.alternate
        )
        if xml:
            rules = list_geofence_layer_rules_xml(workspace, layer_name)
            if not rules or len(rules) == 0:
                rules = list_geofence_layer_rules_xml(workspace, layer.alternate)
            return rules
        rules = list_geofence_layer_rules(workspace, layer_name)
        if not rules or len(rules) == 0:
            rules = list_geofence_layer_rules(workspace, layer.alternate)
        return rules

    def delete_rules(self, ids):
        self.set_has_committed_changes()
        batch_delete_geofence_layer_rules(ids)

    def update_rule(self, *args, **kwargs):
        self.set_has_committed_changes()
        _update_geofence_rule(*args, **kwargs)

    def restore_saved_rules(self, fail_silently):
        for rule in self.safe_point_rules:
            try:
                rule.attrib.pop("id")
                _create_geofence_rule(etree.tostring(rule))
            except GeofenceRequestError as exc:
                user = rule.find("userName").text
                layer_name = rule.find("layer").text
                msg = (
                    f"Could not ADD GeoServer User {user} Rule for "
                    f"Layer {layer_name}: '{exc.detail}'"
                )
                if 'Duplicate Rule' in exc.detail:
                    logger.debug(msg)
                elif not fail_silently:
                    raise

    def set_invalidate_cache(self):
        set_geofence_invalidate_cache()

    def toggle_layer_cache(self, *args, **kwags):
        toggle_layer_cache(*args, **kwags)

    def rollback(self):
        if self.has_committed_changes:
            try:
                self.set_invalidate_cache()
                self.purge_rules()
                self.restore_saved_rules(fail_silently=True)
                self.__has_committed_changes = False
                return True
            except Exception as e:
                logger.debug(e)
                return False
        else:
            return True


class GeofenceLayerRulesUnitOfWork(object):
    def __init__(self, geofence_adapter):
        self.adapter = geofence_adapter
        self.requests_list = []
        self.nested_contexts = 0
        self.adapter_requests_map = {
            "purge_rules": self.adapter.purge_rules,
            "delete_rules": self.adapter.delete_rules,
            "update_rule": self.adapter.update_rule,
            "set_invalidate_cache": self.adapter.set_invalidate_cache,
            "toggle_layer_cache": self.adapter.toggle_layer_cache,
        }

    def __enter__(self):
        self.nested_contexts += 1
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        self.nested_contexts -= 1
        if self.nested_contexts == 0:
            if not exc_type:
                self._execute_requests()
            else:
                self.rollback()

    def _execute_requests(self):
        for request in self.requests_list:
            self.adapter_requests_map[request["name"]](
                *request["args"], **request["kwargs"]
            )

    def rollback(self):
        self.adapter.rollback()
        self.requests_list = []

    def _add_request(self, request_details):
        self.requests_list.append(request_details)

    def purge_rules(self, *args, **kwargs):
        self._add_request(
            {
                "name": "purge_rules",
                "args": args,
                "kwargs": kwargs,
            }
        )

    def delete_rules(self, *args, **kwargs):
        self._add_request(
            {
                "name": "delete_rules",
                "args": args,
                "kwargs": kwargs,
            }
        )

    def update_rule(self, *args, **kwargs):
        self._add_request(
            {
                "name": "update_rule",
                "args": args,
                "kwargs": kwargs,
            }
        )

    def set_invalidate_cache(self, *args, **kwargs):
        self._add_request(
            {
                "name": "set_invalidate_cache",
                "args": args,
                "kwargs": kwargs,
            }
        )

    def toggle_layer_cache(self, *args, **kwargs):
        self._add_request(
            {
                "name": "toggle_layer_cache",
                "args": args,
                "kwargs": kwargs,
            }
        )


def get_visible_resources(queryset,
                          user,
                          request=None,
                          metadata_only=False,
                          admin_approval_required=False,
                          unpublished_not_visible=False,
                          private_groups_not_visibile=False):
    # Get the list of objects the user has access to
    is_admin = user.is_superuser if user and user.is_authenticated else False
    anonymous_group = None
    public_groups = GroupProfile.objects.exclude(access="private").values('group')
    groups = []
    group_list_all = []
    try:
        group_list_all = user.group_list_all().values('group')
    except Exception:
        pass

    try:
        anonymous_group = Group.objects.get(name='anonymous')
        if anonymous_group and anonymous_group not in groups:
            groups.append(anonymous_group)
    except Exception:
        pass

    # Hide Dirty State Resources
    filter_set = queryset.filter(
        Q(dirty_state=False) & Q(metadata_only=metadata_only))

    if not is_admin:
        if user:
            _allowed_resources = get_objects_for_user(user, 'base.view_resourcebase')
            filter_set = filter_set.filter(id__in=_allowed_resources.values('id'))

        if admin_approval_required:
            if not user or not user.is_authenticated or user.is_anonymous:
                filter_set = filter_set.filter(
                    Q(is_published=True) |
                    Q(group__in=public_groups) |
                    Q(group__in=groups)
                ).exclude(is_approved=False)

        # Hide Unpublished Resources to Anonymous Users
        if unpublished_not_visible:
            if not user or not user.is_authenticated or user.is_anonymous:
                filter_set = filter_set.exclude(is_published=False)

        # Hide Resources Belonging to Private Groups
        if private_groups_not_visibile:
            private_groups = GroupProfile.objects.filter(access="private").values('group')
            if user and user.is_authenticated:
                filter_set = filter_set.exclude(
                    Q(group__in=private_groups) & ~(
                        Q(owner__username__iexact=str(user)) | Q(group__in=group_list_all))
                )
            else:
                filter_set = filter_set.exclude(group__in=private_groups)

    return filter_set


def get_users_with_perms(obj):
    """
    Override of the Guardian get_users_with_perms
    """
    from .permissions import (VIEW_PERMISSIONS, ADMIN_PERMISSIONS, LAYER_ADMIN_PERMISSIONS, SERVICE_PERMISSIONS)
    ctype = ContentType.objects.get_for_model(obj)
    permissions = {}
    PERMISSIONS_TO_FETCH = VIEW_PERMISSIONS + ADMIN_PERMISSIONS + LAYER_ADMIN_PERMISSIONS + SERVICE_PERMISSIONS

    if str(ctype) == 'layer':
        for perm in Permission.objects.filter(codename__in=PERMISSIONS_TO_FETCH, content_type_id=ctype.id):
            permissions[perm.id] = perm.codename
    else:
        for perm in Permission.objects.filter(codename__in=PERMISSIONS_TO_FETCH):
            permissions[perm.id] = perm.codename

    user_model = get_user_obj_perms_model(obj)
    users_with_perms = user_model.objects.filter(object_pk=obj.pk,
                                                 permission_id__in=permissions).values('user_id', 'permission_id')

    users = {}
    for item in users_with_perms:
        if item['user_id'] in users:
            users[item['user_id']].append(permissions[item['permission_id']])
        else:
            users[item['user_id']] = [permissions[item['permission_id']], ]

    profiles = {}
    for profile in get_user_model().objects.filter(id__in=list(users.keys())):
        profiles[profile] = users[profile.id]

    return profiles


def perms_as_set(perm) -> set:
    return perm if isinstance(perm, set) else set(perm if isinstance(perm, list) else [perm])

@on_ogc_backend(geoserver.BACKEND_PACKAGE)
def get_geofence_rules(page=0, entries=1, count=False):
    """Get the number of available GeoFence Cache Rules"""
    try:
        url = settings.OGC_SERVER['default']['LOCATION']
        user = settings.OGC_SERVER['default']['USER']
        passwd = settings.OGC_SERVER['default']['PASSWORD']

        _url = ''
        _headers = {'Content-type': 'application/json'}
        if count:
            """
            curl -X GET -u admin:geoserver \
                http://<host>:<port>/geoserver/rest/geofence/rules/count.json
            """
            _url = f"{url}rest/geofence/rules/count.json"
        elif page or entries:
            """
            curl -X GET -u admin:geoserver \
                http://<host>:<port>/geoserver/rest/geofence/rules.json?page={page}&entries={entries}
            """
            _url = f'{url}rest/geofence/rules.json?page={page}&entries={entries}'
        r = requests.get(_url,
                         headers=_headers,
                         auth=HTTPBasicAuth(user, passwd),
                         timeout=10,
                         verify=False)
        if (r.status_code < 200 or r.status_code > 201):
            logger.debug("Could not retrieve GeoFence Rules count.")

        rules_objs = json.loads(r.text)
        return rules_objs
    except Exception:
        tb = traceback.format_exc()
        logger.debug(tb)
        return {'count': -1}


@on_ogc_backend(geoserver.BACKEND_PACKAGE)
def get_geofence_rules_count():
    """Get the number of available GeoFence Cache Rules"""
    rules_objs = get_geofence_rules(count=True)
    rules_count = rules_objs['count']
    return rules_count


@on_ogc_backend(geoserver.BACKEND_PACKAGE)
def get_highest_priority():
    """Get the highest Rules priority"""
    try:
        rules_count = get_geofence_rules_count()
        rules_objs = get_geofence_rules(rules_count - 1)
        if len(rules_objs['rules']) > 0:
            highest_priority = rules_objs['rules'][0]['priority']
        else:
            highest_priority = 0
        return int(highest_priority)
    except Exception:
        tb = traceback.format_exc()
        logger.debug(tb)
        return -1


@on_ogc_backend(geoserver.BACKEND_PACKAGE)
def purge_geofence_all():
    """purge all existing GeoFence Cache Rules"""
    if settings.OGC_SERVER['default']['GEOFENCE_SECURITY_ENABLED']:
        try:
            url = settings.OGC_SERVER['default']['LOCATION']
            user = settings.OGC_SERVER['default']['USER']
            passwd = settings.OGC_SERVER['default']['PASSWORD']
            """
            curl -X GET -u admin:geoserver -H "Content-Type: application/json" \
                  http://<host>:<port>/geoserver/rest/geofence/rules.json
            """
            headers = {'Content-type': 'application/json'}
            r = requests.get(f"{url}rest/geofence/rules.json",
                             headers=headers,
                             auth=HTTPBasicAuth(user, passwd),
                             timeout=10,
                             verify=False)
            if (r.status_code < 200 or r.status_code > 201):
                logger.debug("Could not Retrieve GeoFence Rules")
            else:
                try:
                    rules_objs = json.loads(r.text)
                    rules_count = rules_objs['count']
                    rules = rules_objs['rules']
                    if rules_count > 0:
                        # Delete GeoFence Rules associated to the Layer
                        # curl -X DELETE -u admin:geoserver http://<host>:<port>/geoserver/rest/geofence/rules/id/{r_id}
                        for rule in rules:
                            r = requests.delete(f"{url}rest/geofence/rules/id/{str(rule['id'])}",
                                                headers=headers,
                                                auth=HTTPBasicAuth(user, passwd))
                            if (r.status_code < 200 or r.status_code > 201):
                                msg = f"Could not DELETE GeoServer Rule id[{rule['id']}]"
                                e = Exception(msg)
                                logger.debug(f"Response [{r.status_code}] : {r.text}")
                                raise e
                except Exception:
                    logger.debug(f"Response [{r.status_code}] : {r.text}")
        except Exception:
            tb = traceback.format_exc()
            logger.debug(tb)


@on_ogc_backend(geoserver.BACKEND_PACKAGE)
def batch_delete_geofence_layer_rules(ids):
    """
    curl -X DELETE -u admin:geoserver http://<host>:<port>/geoserver/rest/geofence/rules/id/{r_id}
    """
    url = settings.OGC_SERVER["default"]["LOCATION"]
    user = settings.OGC_SERVER["default"]["USER"]
    passwd = settings.OGC_SERVER["default"]["PASSWORD"]
    headers = {"Content-type": "application/json"}
    auth = HTTPBasicAuth(user, passwd)

    for rule_id in ids:
        resource_url = f"{url}rest/geofence/rules/id/{str(rule_id)}"
        response = requests.delete(resource_url, headers=headers, auth=auth)
        if response.status_code < 200 or response.status_code > 201:
            msg = f"Could not DELETE GeoServer Rule {str(rule_id)}"
            e = Exception(msg)
            logger.debug(f"Response [{response.status_code}] : {response.text}")
            raise e


@on_ogc_backend(geoserver.BACKEND_PACKAGE)
def list_geofence_layer_rules(workspace, layer_name):
    """
    curl -u admin:geoserver
    http://<host>:<port>/geoserver/rest/geofence/rules.json?workspace=geonode&layer={layer}
    """
    url = settings.OGC_SERVER["default"]["LOCATION"]
    user = settings.OGC_SERVER["default"]["USER"]
    passwd = settings.OGC_SERVER["default"]["PASSWORD"]
    headers = {"Content-type": "application/json"}
    auth = HTTPBasicAuth(user, passwd)

    rules = []
    resource_url = f"{url}rest/geofence/rules.json?workspace={workspace}&layer={layer_name}"
    response = requests.get(resource_url, headers=headers, auth=auth, timeout=10, verify=False)
    if response.status_code >= 200 and response.status_code < 300:
        gs_rules = response.json()
        if gs_rules and gs_rules["rules"]:
            for rule in gs_rules["rules"]:
                if rule["layer"] and rule["layer"] == layer_name:
                    rules.append(rule)

    return rules


@on_ogc_backend(geoserver.BACKEND_PACKAGE)
def list_geofence_layer_rules_xml(workspace, layer_name):
    """
    curl -u admin:geoserver
    http://<host>:<port>/geoserver/rest/geofence/rules?workspace=geonode&layer={layer}
    """
    url = settings.OGC_SERVER["default"]["LOCATION"]
    user = settings.OGC_SERVER["default"]["USER"]
    passwd = settings.OGC_SERVER["default"]["PASSWORD"]
    headers = {"Content-type": "application/xml"}
    auth = HTTPBasicAuth(user, passwd)

    rules = []
    resource_url = f"{url}rest/geofence/rules?workspace={workspace}&layer={layer_name}"
    response = requests.get(resource_url, headers=headers, auth=auth, timeout=10, verify=False)
    if response.status_code >= 200 and response.status_code < 300:
        gs_rules = etree.fromstring(response.content)
        for rule in gs_rules:
            layer_field = rule.find("layer")
            if layer_field is not None and hasattr(layer_field, "text") and layer_field.text == layer_name:
                rules.append(rule)

    return rules


@on_ogc_backend(geoserver.BACKEND_PACKAGE)
def purge_geofence_layer_rules(resource):
    """purge layer existing GeoFence Cache Rules"""
    # Scan GeoFence Rules associated to the Layer
    """
    curl -u admin:geoserver
    http://<host>:<port>/geoserver/rest/geofence/rules.json?workspace=geonode&layer={layer}
    """
    layer = resource.layer
    workspace = get_layer_workspace(layer)
    layer_name = layer.name if layer and hasattr(layer, "name") else layer.alternate
    try:
        rules = list_geofence_layer_rules(workspace, layer_name)
        if not rules or len(rules) == 0:
            rules = list_geofence_layer_rules(workspace, layer.alternate)
        batch_delete_geofence_layer_rules([rule["id"] for rule in rules])
    except Exception as e:
        logger.exception(e)


@on_ogc_backend(geoserver.BACKEND_PACKAGE)
def set_geofence_invalidate_cache():
    """invalidate GeoFence Cache Rules"""
    if settings.OGC_SERVER['default']['GEOFENCE_SECURITY_ENABLED']:
        try:
            url = settings.OGC_SERVER['default']['LOCATION']
            user = settings.OGC_SERVER['default']['USER']
            passwd = settings.OGC_SERVER['default']['PASSWORD']
            """
            curl -X GET -u admin:geoserver \
                  http://<host>:<port>/geoserver/rest/ruleCache/invalidate
            """
            r = requests.put(f"{url}rest/ruleCache/invalidate",
                             auth=HTTPBasicAuth(user, passwd))

            if (r.status_code < 200 or r.status_code > 201):
                logger.debug("Could not Invalidate GeoFence Rules.")
                return False
            return True
        except Exception:
            tb = traceback.format_exc()
            logger.debug(tb)
            return False


@on_ogc_backend(geoserver.BACKEND_PACKAGE)
def toggle_layer_cache(layer_name, enable=True, filters=None, formats=None, geofence_uow=None):
    """Disable/enable a GeoServer Tiled Layer Configuration"""
    if geofence_uow:
        geofence_uow.toggle_layer_cache(
            layer_name, enable=enable, filters=filters, formats=formats
        )
        return True
    if settings.OGC_SERVER['default']['GEOFENCE_SECURITY_ENABLED']:
        try:
            url = settings.OGC_SERVER['default']['LOCATION']
            user = settings.OGC_SERVER['default']['USER']
            passwd = settings.OGC_SERVER['default']['PASSWORD']
            """
            curl -v -u admin:geoserver -XGET \
                "http://<host>:<port>/geoserver/gwc/rest/layers/geonode:tasmania_roads.xml"
            """
            r = requests.get(f'{url}gwc/rest/layers/{layer_name}.xml',
                             auth=HTTPBasicAuth(user, passwd))

            if (r.status_code < 200 or r.status_code > 201):
                logger.debug(f"Could not Retrieve {layer_name} Cache.")
                return False
            try:
                xml_content = r.content
                tree = dlxml.fromstring(xml_content)

                gwc_id = tree.find('id')
                tree.remove(gwc_id)

                gwc_enabled = tree.find('enabled')
                if gwc_enabled is None:
                    gwc_enabled = etree.Element('enabled')
                    tree.append(gwc_enabled)
                gwc_enabled.text = str(enable).lower()

                gwc_mimeFormats = tree.find('mimeFormats')
                # Returns an element instance or None
                if gwc_mimeFormats is not None and len(gwc_mimeFormats):
                    tree.remove(gwc_mimeFormats)

                if formats is not None:
                    for format in formats:
                        gwc_format = etree.Element('string')
                        gwc_format.text = format
                        gwc_mimeFormats.append(gwc_format)

                    tree.append(gwc_mimeFormats)

                gwc_parameterFilters = tree.find('parameterFilters')
                if filters is None:
                    tree.remove(gwc_parameterFilters)
                else:
                    for filter in filters:
                        for k, v in filter.items():
                            """
                            <parameterFilters>
                                <styleParameterFilter>
                                    <key>STYLES</key>
                                    <defaultValue/>
                                </styleParameterFilter>
                            </parameterFilters>
                            """
                            gwc_parameter = etree.Element(k)
                            for parameter_key, parameter_value in v.items():
                                gwc_parameter_key = etree.Element('key')
                                gwc_parameter_key.text = parameter_key
                                gwc_parameter_value = etree.Element('defaultValue')
                                gwc_parameter_value.text = parameter_value

                                gwc_parameter.append(gwc_parameter_key)
                                gwc_parameter.append(gwc_parameter_value)
                            gwc_parameterFilters.append(gwc_parameter)

                """
                curl -v -u admin:geoserver -XPOST \
                    -H "Content-type: text/xml" -d @poi.xml \
                        "http://localhost:8080/geoserver/gwc/rest/layers/tiger:poi.xml"
                """
                headers = {'Content-type': 'text/xml'}
                payload = ET.tostring(tree)
                r = requests.post(f'{url}gwc/rest/layers/{layer_name}.xml',
                                  headers=headers,
                                  data=payload,
                                  auth=HTTPBasicAuth(user, passwd))
                if (r.status_code < 200 or r.status_code > 201):
                    logger.debug(f"Could not Update {layer_name} Cache.")
                    return False
            except Exception:
                tb = traceback.format_exc()
                logger.debug(tb)
                return False
            return True
        except Exception:
            tb = traceback.format_exc()
            logger.debug(tb)
            return False


@on_ogc_backend(geoserver.BACKEND_PACKAGE)
def delete_layer_cache(layer_name):
    """Delete a GeoServer Tiled Layer Configuration and all the cache"""
    if settings.OGC_SERVER['default']['GEOFENCE_SECURITY_ENABLED']:
        try:
            url = settings.OGC_SERVER['default']['LOCATION']
            user = settings.OGC_SERVER['default']['USER']
            passwd = settings.OGC_SERVER['default']['PASSWORD']
            """
            curl -v -u admin:geoserver -XDELETE \
                "http://<host>:<port>/geoserver/gwc/rest/layers/geonode:tasmania_roads.xml"
            """
            r = requests.delete(f'{url}gwc/rest/layers/{layer_name}.xml',
                                auth=HTTPBasicAuth(user, passwd))

            if (r.status_code < 200 or r.status_code > 201):
                logger.debug(f"Could not Delete {layer_name} Cache.")
                return False
            return True
        except Exception:
            tb = traceback.format_exc()
            logger.debug(tb)
            return False


@on_ogc_backend(geoserver.BACKEND_PACKAGE)
def set_geowebcache_invalidate_cache(layer_alternate, cat=None):
    """invalidate GeoWebCache Cache Rules"""
    if layer_alternate is not None and len(layer_alternate) and "None" not in layer_alternate:
        try:
            if cat is None or cat.get_layer(layer_alternate) is not None:
                url = settings.OGC_SERVER['default']['LOCATION']
                user = settings.OGC_SERVER['default']['USER']
                passwd = settings.OGC_SERVER['default']['PASSWORD']
                """
                curl -v -u admin:geoserver \
                -H "Content-type: text/xml" \
                -d "<truncateLayer><layerName>{layer_alternate}</layerName></truncateLayer>" \
                http://localhost:8080/geoserver/gwc/rest/masstruncate
                """
                headers = {'Content-type': 'text/xml'}
                payload = f"<truncateLayer><layerName>{layer_alternate}</layerName></truncateLayer>"
                r = requests.post(
                    f"{url}gwc/rest/masstruncate",
                    headers=headers,
                    data=payload,
                    auth=HTTPBasicAuth(user, passwd))
                if (r.status_code < 200 or r.status_code > 201):
                    logger.debug(f"Could not Truncate GWC Cache for Layer '{layer_alternate}'.")
        except Exception:
            tb = traceback.format_exc()
            logger.debug(tb)


@on_ogc_backend(geoserver.BACKEND_PACKAGE)
def set_geofence_all(instance):
    """assign access permissions to all users

    This method is only relevant to Layer instances that have their
    underlying data managed by geoserver, meaning:

    * layers that are not associated with a Service
    * layers that are associated with a Service that is being CASCADED through
      geoserver

    """
    resource = instance.get_self_resource()
    logger.debug(f"Inside set_geofence_all for instance {instance}")
    workspace = get_layer_workspace(resource.layer)
    layer_name = resource.layer.name if resource.layer and hasattr(resource.layer, 'name') \
        else resource.layer.alternate
    logger.debug(f"going to work in workspace {workspace}")
    try:
        url = settings.OGC_SERVER['default']['LOCATION']
        user = settings.OGC_SERVER['default']['USER']
        passwd = settings.OGC_SERVER['default']['PASSWORD']

        # Create GeoFence Rules for ANONYMOUS to the Layer
        """
        curl -X POST -u admin:geoserver -H "Content-Type: text/xml" -d \
        "<Rule><workspace>geonode</workspace><layer>{layer}</layer><access>ALLOW</access></Rule>" \
        http://<host>:<port>/geoserver/rest/geofence/rules
        """
        headers = {'Content-type': 'application/xml'}
        payload = _get_geofence_payload(
            layer_name=layer_name,
            workspace=workspace,
            access="ALLOW"
        )
        response = requests.post(
            f"{url}rest/geofence/rules",
            headers=headers,
            data=payload,
            auth=HTTPBasicAuth(user, passwd)
        )
        if response.status_code not in (200, 201):
            logger.debug(
                f"Response {response.status_code} : {response.text}")
            raise RuntimeError("Could not ADD GeoServer ANONYMOUS Rule "
                               f"for Layer {layer_name}")
    except Exception:
        tb = traceback.format_exc()
        logger.debug(tb)
    finally:
        if not getattr(settings, 'DELAYED_SECURITY_SIGNALS', False):
            set_geofence_invalidate_cache()
        else:
            resource.set_dirty_state()


@on_ogc_backend(geoserver.BACKEND_PACKAGE)
def sync_geofence_with_guardian(layer, perms, user=None, group=None, group_perms=None, geofence_uow=None):
    """
    Sync Guardian permissions to GeoFence.
    """
    _layer_name = layer.name if layer and hasattr(layer, 'name') else layer.alternate
    _layer_workspace = get_layer_workspace(layer)
    # Create new rule-set
    gf_services = _get_gf_services(layer, perms)

    gf_requests = {}
    if 'change_layer_data' not in perms:
        _skip_perm = False
        if user and group_perms:
            if isinstance(user, str):
                user = get_user_model().objects.get(username=user)
            user_groups = list(user.groups.all().values_list('name', flat=True))
            for _group, _perm in group_perms.items():
                if 'change_layer_data' in _perm and _group in user_groups:
                    _skip_perm = True
                    break
        if not _skip_perm:
            gf_requests["WFS"] = {
                "TRANSACTION": False,
                "LOCKFEATURE": False,
                "GETFEATUREWITHLOCK": False
            }
    _user = None
    _group = None
    users_geolimits = None
    groups_geolimits = None
    anonymous_geolimits = None

    _group, _user, _disable_cache, users_geolimits, groups_geolimits, anonymous_geolimits = get_user_geolimits(layer, user, group, gf_services)

    if _disable_cache:
        # Re-order dictionary
        # - if geo-limits have been defined for this user/group, the "*" rule must be the first one
        gf_services_limits_first = {"*": gf_services.pop('*')}
        gf_services_limits_first.update(gf_services)
        gf_services = gf_services_limits_first

    for service, allowed in gf_services.items():
        if layer and _layer_name and allowed:
            if _user:
                logger.debug(f"Adding 'user' to geofence the rule: {layer} {service} {_user}")
                _wkt = None
                if users_geolimits and users_geolimits.count():
                    _wkt = users_geolimits.last().wkt
                if service in gf_requests:
                    for request, enabled in gf_requests[service].items():
                        _update_geofence_rule(_layer_name, _layer_workspace,
                                              service, request=request, user=_user, allow=enabled, geofence_uow=geofence_uow)
                _update_geofence_rule(_layer_name, _layer_workspace, service, user=_user, geo_limit=_wkt, geofence_uow=geofence_uow)
            elif not _group:
                logger.debug(f"Adding to geofence the rule: {layer} {service} *")
                _wkt = None
                if anonymous_geolimits and anonymous_geolimits.count():
                    _wkt = anonymous_geolimits.last().wkt
                if service in gf_requests:
                    for request, enabled in gf_requests[service].items():
                        _update_geofence_rule(_layer_name, _layer_workspace,
                                              service, request=request, user=_user, allow=enabled, geofence_uow=geofence_uow)
                _update_geofence_rule(_layer_name, _layer_workspace, service, geo_limit=_wkt, geofence_uow=geofence_uow)
                if service in gf_requests:
                    for request, enabled in gf_requests[service].items():
                        _update_geofence_rule(_layer_name, _layer_workspace,
                                              service, request=request, user=_user, allow=enabled, geofence_uow=geofence_uow)
            if _group:
                logger.debug(f"Adding 'group' to geofence the rule: {layer} {service} {_group}")
                _wkt = None
                if groups_geolimits and groups_geolimits.count():
                    _wkt = groups_geolimits.last().wkt
                if service in gf_requests:
                    for request, enabled in gf_requests[service].items():
                        _update_geofence_rule(_layer_name, _layer_workspace,
                                              service, request=request, group=_group, allow=enabled, geofence_uow=geofence_uow)
                _update_geofence_rule(_layer_name, _layer_workspace, service, group=_group, geo_limit=_wkt, geofence_uow=geofence_uow)
                if service in gf_requests:
                    for request, enabled in gf_requests[service].items():
                        _update_geofence_rule(_layer_name, _layer_workspace,
                                              service, request=request, group=_group, allow=enabled, geofence_uow=geofence_uow)

    if not getattr(settings, 'DELAYED_SECURITY_SIGNALS', False):
        if geofence_uow:
            geofence_uow.set_invalidate_cache()
        else:
            set_geofence_invalidate_cache()
    else:
        layer.set_dirty_state()


def get_user_geolimits(layer, user, group, gf_services):
    _user = None
    _group = None
    users_geolimits = None
    groups_geolimits = None
    anonymous_geolimits = None
    _disable_layer_cache = False
    if user:
        _user = user if isinstance(user, str) else user.username
        users_geolimits = layer.users_geolimits.filter(user=get_user_model().objects.get(username=_user))
        gf_services["*"] = users_geolimits.count() > 0 if not gf_services["*"] else gf_services["*"]
        _disable_layer_cache = users_geolimits.count() > 0

    if group:
        _group = group if isinstance(group, str) else group.name
        if GroupProfile.objects.filter(group__name=_group).count() == 1:
            groups_geolimits = layer.groups_geolimits.filter(group=GroupProfile.objects.get(group__name=_group))
            gf_services["*"] = groups_geolimits.count() > 0 if not gf_services["*"] else gf_services["*"]
            _disable_layer_cache = groups_geolimits.count() > 0

    if not user and not group:
        anonymous_geolimits = layer.users_geolimits.filter(user=get_anonymous_user())
        gf_services["*"] = anonymous_geolimits.count() > 0 if not gf_services["*"] else gf_services["*"]
        _disable_layer_cache = anonymous_geolimits.count() > 0
    return _group, _user, _disable_layer_cache, users_geolimits, groups_geolimits, anonymous_geolimits


def _get_gf_services(layer, perms):
    gf_services = {}
    gf_services["WMS"] = 'view_resourcebase' in perms or 'change_layer_style' in perms
    gf_services["GWC"] = 'view_resourcebase' in perms or 'change_layer_style' in perms
    gf_services["WFS"] = ('download_resourcebase' in perms or 'change_layer_data' in perms) \
        and layer.is_vector()
    gf_services["WCS"] = ('download_resourcebase' in perms or 'change_layer_data' in perms) \
        and not layer.is_vector()
    gf_services["WPS"] = 'download_resourcebase' in perms or 'change_layer_data' in perms
    gf_services["*"] = 'download_resourcebase' in perms and \
        ('view_resourcebase' in perms or 'change_layer_style' in perms)

    return gf_services


def set_owner_permissions(resource, members=None):
    """assign all admin permissions to the owner"""
    from .permissions import (VIEW_PERMISSIONS, ADMIN_PERMISSIONS, LAYER_ADMIN_PERMISSIONS, SERVICE_PERMISSIONS)
    if resource.polymorphic_ctype:
        # Owner & Manager Admin Perms
        admin_perms = VIEW_PERMISSIONS + ADMIN_PERMISSIONS
        for perm in admin_perms:
            if not settings.RESOURCE_PUBLISHING and not settings.ADMIN_MODERATE_UPLOADS:
                assign_perm(perm, resource.owner, resource.get_self_resource())
            elif perm not in {'change_resourcebase_permissions', 'publish_resourcebase'}:
                assign_perm(perm, resource.owner, resource.get_self_resource())
            if members:
                for user in members:
                    assign_perm(perm, user, resource.get_self_resource())

        # Set the GeoFence Owner Rule
        if resource.polymorphic_ctype.name == 'layer':
            for perm in LAYER_ADMIN_PERMISSIONS:
                assign_perm(perm, resource.owner, resource.layer)
                if members:
                    for user in members:
                        assign_perm(perm, user, resource.layer)

        if resource.polymorphic_ctype.name == 'service':
            for perm in SERVICE_PERMISSIONS:
                assign_perm(perm, resource.owner, resource.service)
                if members:
                    for user in members:
                        assign_perm(perm, user, resource.service)


def remove_object_permissions(instance, purge=True, geofence_uow=None):
    """Remove object permissions on given resource.

    If is a layer removes the layer specific permissions then the
    resourcebase permissions

    """
    from guardian.models import UserObjectPermission, GroupObjectPermission
    resource = instance.get_self_resource()
    try:
        if hasattr(resource, "layer"):
            UserObjectPermission.objects.filter(
                content_type=ContentType.objects.get_for_model(resource.layer),
                object_pk=instance.id
            ).delete()
            GroupObjectPermission.objects.filter(
                content_type=ContentType.objects.get_for_model(resource.layer),
                object_pk=instance.id
            ).delete()
    except (ObjectDoesNotExist, RuntimeError):
        pass  # This layer is not manageable by geofence
    except Exception:
        tb = traceback.format_exc()
        logger.debug(tb)
    finally:
        if purge:
            if instance.polymorphic_ctype.name == 'layer':
                if settings.OGC_SERVER['default'].get("GEOFENCE_SECURITY_ENABLED", False):
                    if not getattr(settings, 'DELAYED_SECURITY_SIGNALS', False):
                        if geofence_uow:
                            geofence_uow.purge_rules()
                            geofence_uow.set_invalidate_cache()
                        else:
                            purge_geofence_layer_rules(resource)
                            set_geofence_invalidate_cache()
                    else:
                        resource.set_dirty_state()
    UserObjectPermission.objects.filter(content_type=ContentType.objects.get_for_model(resource),
                                        object_pk=instance.id).delete()
    GroupObjectPermission.objects.filter(content_type=ContentType.objects.get_for_model(resource),
                                         object_pk=instance.id).delete()


def _get_geofence_payload(layer_name, workspace, access, user=None, group=None,
                          service=None, request=None, geo_limit=None):
    highest_priority = get_highest_priority()
    root_el = etree.Element("Rule")
    username_el = etree.SubElement(root_el, "userName")
    if user is not None:
        username_el.text = user
    else:
        username_el.text = ''
    priority_el = etree.SubElement(root_el, "priority")
    priority_el.text = str(highest_priority if highest_priority >= 0 else 0)
    if group is not None:
        role_el = etree.SubElement(root_el, "roleName")
        role_el.text = f"ROLE_{group.upper()}"
    workspace_el = etree.SubElement(root_el, "workspace")
    workspace_el.text = workspace
    layer_el = etree.SubElement(root_el, "layer")
    layer_el.text = layer_name
    if service is not None and service != "*":
        service_el = etree.SubElement(root_el, "service")
        service_el.text = service
    if request is not None and request != "*":
        service_el = etree.SubElement(root_el, "request")
        service_el.text = request
    if service and service == "*" and geo_limit is not None and geo_limit != "":
        access_el = etree.SubElement(root_el, "access")
        access_el.text = "LIMIT"
        limits = etree.SubElement(root_el, "limits")
        catalog_mode = etree.SubElement(limits, "catalogMode")
        catalog_mode.text = "MIXED"
        allowed_area = etree.SubElement(limits, "allowedArea")
        allowed_area.text = geo_limit
    else:
        access_el = etree.SubElement(root_el, "access")
        access_el.text = access
    return etree.tostring(root_el)


def _create_geofence_rule(payload):
    username = settings.OGC_SERVER['default']['USER']
    password = settings.OGC_SERVER['default']['PASSWORD']
    url = settings.OGC_SERVER['default']['LOCATION']
    headers = {'Content-type': 'application/xml'}
    auth = HTTPBasicAuth(username=username, password=password)

    logger.debug(f"request data: {payload}")
    resource_url = f"{url}rest/geofence/rules"
    response = requests.post(
        resource_url,
        data=payload,
        headers=headers,
        auth=auth
    )
    logger.debug(f"response status_code: {response.status_code}")
    if response.status_code not in (200, 201):
        raise GeofenceRequestError(detail=response.text)


def _update_geofence_rule(layer_name, workspace,
                          service, request=None,
                          user=None, group=None,
                          geo_limit=None, allow=True,
                          geofence_uow=None):
    if geofence_uow:
        geofence_uow.update_rule(
            layer_name, workspace, service,
            request=request, user=user, group=group,
            geo_limit=geo_limit, allow=allow
        )
        return None
    payload = _get_geofence_payload(
        layer_name=layer_name,
        workspace=workspace,
        access="ALLOW" if allow else "DENY",
        user=user,
        group=group,
        service=service,
        request=request,
        geo_limit=geo_limit
    )
    try:
        _create_geofence_rule(payload)
    except GeofenceRequestError as exc:
        msg = (
            f"Could not ADD GeoServer User {user} Rule for "
            f"Layer {layer_name}: '{exc.detail}'"
        )
        if 'Duplicate Rule' in exc.detail:
            logger.debug(msg)
        else:
            raise RuntimeError(msg)


def sync_resources_with_guardian(resource=None):
    """
    Sync resources with Guardian and clear their dirty state
    """

    from geonode.base.models import ResourceBase
    from geonode.layers.models import Layer

    if resource:
        dirty_resources = ResourceBase.objects.filter(id=resource.id)
    else:
        dirty_resources = ResourceBase.objects.filter(dirty_state=True)
    if dirty_resources and dirty_resources.count() > 0:
        logger.debug(" --------------------------- synching with guardian!")
        for r in dirty_resources:
            if r.polymorphic_ctype.name == 'layer':
                layer = None
                try:
                    purge_geofence_layer_rules(r)
                    layer = Layer.objects.get(id=r.id)
                    perm_spec = layer.get_all_level_info()
                    # All the other users
                    if 'users' in perm_spec:
                        for user, perms in perm_spec['users'].items():
                            user = get_user_model().objects.get(username=user)
                            # Set the GeoFence User Rules
                            geofence_user = str(user)
                            if "AnonymousUser" in geofence_user or get_anonymous_user() in geofence_user:
                                geofence_user = None
                            sync_geofence_with_guardian(layer, perms, user=geofence_user)
                    # All the other groups
                    if 'groups' in perm_spec:
                        for group, perms in perm_spec['groups'].items():
                            group = Group.objects.get(name=group)
                            # Set the GeoFence Group Rules
                            sync_geofence_with_guardian(layer, perms, group=group)
                    r.clear_dirty_state()
                except Exception as e:
                    logger.exception(e)
                    logger.warn(f"!WARNING! - Failure Synching-up Security Rules for Resource [{r}]")


def get_resources_with_perms(user, filter_options={}, shortcut_kwargs={}):
    """
    Returns resources a user has access to.
    """

    from geonode.base.models import ResourceBase

    if settings.SKIP_PERMS_FILTER:
        resources = ResourceBase.objects.all()
    else:
        resources = get_objects_for_user(
            user,
            'base.view_resourcebase',
            **shortcut_kwargs
        )

    resources_with_perms = get_visible_resources(
        resources,
        user,
        admin_approval_required=settings.ADMIN_MODERATE_UPLOADS,
        unpublished_not_visible=settings.RESOURCE_PUBLISHING,
        private_groups_not_visibile=settings.GROUP_PRIVATE_RESOURCES)

    if filter_options:
        if resources_with_perms and resources_with_perms.count() > 0:
            if filter_options.get('title_filter'):
                resources_with_perms = resources_with_perms.filter(
                    title__icontains=filter_options.get('title_filter')
                )
            type_filters = []
            if filter_options.get('type_filter'):
                _type_filter = filter_options.get('type_filter')
                if _type_filter:
                    type_filters.append(_type_filter)
                # get subtypes for geoapps
                if _type_filter == 'geoapp':
                    type_filters.extend(get_geoapp_subtypes())

            if type_filters:
                resources_with_perms = resources_with_perms.filter(
                    polymorphic_ctype__model__in=type_filters
                )

    return resources_with_perms


def get_geoapp_subtypes():
    """
    Returns a list of geoapp subtypes.
    eg ['geostory']
    """

    from geonode.geoapps.models import GeoApp

    subtypes = []
    for label, app in apps.app_configs.items():
        if hasattr(app, 'type') and app.type == 'GEONODE_APP':
            if hasattr(app, 'default_model'):
                _model = apps.get_model(label, app.default_model)
                if issubclass(_model, GeoApp):
                    subtypes.append(_model.__name__.lower())
    return subtypes


def skip_registered_members_common_group(user_group):
    from geonode.groups.conf import settings as groups_settings
    if groups_settings.AUTO_ASSIGN_REGISTERED_MEMBERS_TO_REGISTERED_MEMBERS_GROUP_NAME:
        _members_group_name = groups_settings.REGISTERED_MEMBERS_GROUP_NAME
        if (settings.RESOURCE_PUBLISHING or settings.ADMIN_MODERATE_UPLOADS) and \
                _members_group_name == user_group.name:
            return True
    return False

def get_user_groups(owner, group=None):
    """
    Returns all the groups belonging to the "owner"
    """
    user_groups = Group.objects.filter(name__in=owner.groupmember_set.values_list("group__slug", flat=True))
    if group:
        user_groups = chain(user_groups, [group.group if hasattr(group, 'group') else group])
    return list(set(user_groups))


def get_user_visible_groups(user, include_public_invite: bool = False):
    """
    Retrieves all the groups accordingly to the following conditions:
    - The user is member of
    - The group is public
    """
    from geonode.groups.models import GroupProfile

    metadata_author_groups = []
    if user.is_superuser or user.is_staff:
        metadata_author_groups = GroupProfile.objects.all()
    else:
        if include_public_invite:
            group_profile_queryset = GroupProfile.objects.exclude(
                access="private")
        else:
            group_profile_queryset = GroupProfile.objects.exclude(
                access="private").exclude(access="public-invite")
        try:
            all_metadata_author_groups = chain(
                user.group_list_all(),
                group_profile_queryset)
        except Exception:
            all_metadata_author_groups = group_profile_queryset
        [metadata_author_groups.append(item) for item in all_metadata_author_groups
            if item not in metadata_author_groups]
    return metadata_author_groups


AdminViewPermissionsSet = collections.namedtuple('AdminViewPermissionsSet', [
    'admin_perms', 'view_perms'
])


ResourceGroupsAndMembersSet = collections.namedtuple('ResourceGroupsAndMembersSet', [
    'anonymous_group', 'registered_members_group', 'owner_groups', 'resource_groups', 'managers'
])

class AdvancedSecurityWorkflowManager:
  
    @staticmethod
    def is_anonymous_can_view():
        return settings.DEFAULT_ANONYMOUS_VIEW_PERMISSION

    @staticmethod
    def is_anonymous_can_download():
        return settings.DEFAULT_ANONYMOUS_DOWNLOAD_PERMISSION

    @staticmethod
    def is_group_private_mode():
        return settings.GROUP_PRIVATE_RESOURCES

    @staticmethod
    def is_manager_publish_mode():
        return settings.RESOURCE_PUBLISHING

    @staticmethod
    def is_admin_moderate_mode():
        return settings.ADMIN_MODERATE_UPLOADS

    @staticmethod
    def is_auto_publishing_workflow():
        """
          **AUTO PUBLISHING**
            - `RESOURCE_PUBLISHING = False`
            - `ADMIN_MODERATE_UPLOADS = False`

            - When user creates a resource:
              - OWNER gets all the owner permissions (publish resource included)
              - ANONYMOUS can view and download
            - No change to the Group Manager is applied
        """
        return not settings.RESOURCE_PUBLISHING and not settings.ADMIN_MODERATE_UPLOADS

    @staticmethod
    def is_simple_publishing_workflow():
        """
          **SIMPLE PUBLISHING**
            - `RESOURCE_PUBLISHING = True` (Autopublishing is disabled)
            - `ADMIN_MODERATE_UPLOADS = False`

            - When user creates a resource:
              - OWNER gets all the owner permissions (`publish_resource` and `change_resourcebase_permissions` INCLUDED)
              - Group MANAGERS of the user's groups will get the owner permissions (`publish_resource` EXCLUDED)
              - Group MEMBERS of the user's groups will get the `view_resourcebase`, `download_resourcebase` permission
              - ANONYMOUS can not view and download if the resource is not published

            - When resource has a group assigned:
              - OWNER gets all the owner permissions (`publish_resource` and `change_resourcebase_permissions` INCLUDED)
              - Group MANAGERS of the *resource's group* will get the owner permissions (`publish_resource` EXCLUDED)
              - Group MEMBERS of the *resource's group* will get the `view_resourcebase`, `download_resourcebase` permission
        """
        return settings.RESOURCE_PUBLISHING and not settings.ADMIN_MODERATE_UPLOADS

    @staticmethod
    def is_advanced_workflow():
        """
          **ADVANCED WORKFLOW**
            - `RESOURCE_PUBLISHING = True`
            - `ADMIN_MODERATE_UPLOADS = True`

            - When user creates a resource:
              - OWNER gets all the owner permissions (`publish_resource` and `change_resourcebase_permissions` EXCLUDED)
              - Group MANAGERS of the user's groups will get the owner permissions (`publish_resource` INCLUDED)
              - Group MEMBERS of the user's groups will get the `view_resourcebase`, `download_resourcebase` permission
              - ANONYMOUS can not view and download if the resource is not published

            - When resource has a group assigned:
              - OWNER gets all the owner permissions (`publish_resource` and `change_resourcebase_permissions` EXCLUDED)
              - Group MANAGERS of the resource's group will get the owner permissions (`publish_resource` INCLUDED)
              - Group MEMBERS of the resource's group will get the `view_resourcebase`, `download_resourcebase` permission
        """
        return settings.RESOURCE_PUBLISHING and settings.ADMIN_MODERATE_UPLOADS

    @staticmethod
    def is_simplified_workflow():
        """
          **SIMPLIFIED WORKFLOW**
            - `RESOURCE_PUBLISHING = False`
            - `ADMIN_MODERATE_UPLOADS = True`

            - **NOTE**: Is it even possibile? when the resource is automatically published, can it be un-published?
            If this combination is not allowed, we should either stop the process when reading the settings or log a warning and force a safe combination.

            - When user creates a resource:
              - OWNER gets all the owner permissions (`publish_resource` and `change_resourcebase_permissions` INCLUDED)
              - Group MANAGERS of the user's groups will get the owner permissions (`publish_resource` INCLUDED)
              - Group MEMBERS of the user's group will get the `view_resourcebase`, `download_resourcebase` permission
              - ANONYMOUS can view and download
        """
        return not settings.RESOURCE_PUBLISHING and settings.ADMIN_MODERATE_UPLOADS

    @staticmethod
    def is_allowed_to_approve(user, resource):
        ResourceGroupsAndMembersSet = AdvancedSecurityWorkflowManager.compute_resource_groups_and_members_set(
            resource.uuid, instance=resource, group=resource.group)
        is_superuser = user.is_superuser
        is_owner = user == resource.owner
        is_manager = user in ResourceGroupsAndMembersSet.managers

        can_change_metadata = user.has_perm(
            'change_resourcebase_metadata',
            resource.get_self_resource())

        if is_superuser:
            return True
        elif AdvancedSecurityWorkflowManager.is_admin_moderate_mode():
            return is_manager and can_change_metadata
        else:
            return is_owner or is_manager or can_change_metadata

    @staticmethod
    def is_allowed_to_publish(user, resource):
        ResourceGroupsAndMembersSet = AdvancedSecurityWorkflowManager.compute_resource_groups_and_members_set(
            resource.uuid, instance=resource, group=resource.group)
        is_superuser = user.is_superuser
        is_owner = user == resource.owner
        is_manager = user in ResourceGroupsAndMembersSet.managers

        can_publish = user.has_perm(
            'publish_resourcebase',
            resource.get_self_resource())

        if is_superuser:
            return True
        elif AdvancedSecurityWorkflowManager.is_manager_publish_mode():
            return is_manager and can_publish
        else:
            return is_owner or is_manager or can_publish

    @staticmethod
    def assignable_perm_condition(perm, resource_type):
        _assignable_perm_policy_condition = (perm in DOWNLOAD_PERMISSIONS and resource_type in DOWNLOADABLE_RESOURCES) or \
            (perm in LAYER_EDIT_DATA_PERMISSIONS and resource_type in DATA_EDITABLE_RESOURCES_SUBTYPES) or \
            (perm not in (DOWNLOAD_PERMISSIONS + LAYER_EDIT_DATA_PERMISSIONS))
        logger.debug(f" perm: {perm} - resource_type: {resource_type} --> assignable: {_assignable_perm_policy_condition}")
        return _assignable_perm_policy_condition

    @staticmethod
    def get_instance(uuid: str):
        from geonode.base.models import ResourceBase
        return ResourceBase.objects.filter(uuid=uuid).first()

    @staticmethod
    def compute_admin_and_view_permissions_set(uuid: str, /, instance=None) -> AdminViewPermissionsSet:
        """
        returns a copy of the ADMIN_PERMISSIONS and VIEW_PERMISISONS of a resource accordinlgy to:
         - The resource_type
         - The resource_subtype
        """
        _resource = instance or AdvancedSecurityWorkflowManager.get_instance(uuid)
        view_perms = []
        admin_perms = []
        if _resource.polymorphic_ctype:
            _resource_type = _resource.resource_type or _resource.polymorphic_ctype.name
            _resource_subtype = _resource.subtype
            view_perms = VIEW_PERMISSIONS.copy()
            if _resource_type in DOWNLOADABLE_RESOURCES:
                view_perms += DOWNLOAD_PERMISSIONS.copy()

            admin_perms = ADMIN_PERMISSIONS.copy()
            if _resource.polymorphic_ctype.name == 'layer':
                if _resource_subtype in DATA_EDITABLE_RESOURCES_SUBTYPES:
                    admin_perms += LAYER_EDIT_DATA_PERMISSIONS.copy()
                if _resource_subtype in DATA_STYLABLE_RESOURCES_SUBTYPES:
                    admin_perms += LAYER_EDIT_STYLE_PERMISSIONS.copy()

            if _resource.polymorphic_ctype.name == 'service':
                admin_perms += SERVICE_PERMISSIONS.copy()

        return AdminViewPermissionsSet(admin_perms, view_perms)

    @staticmethod
    def compute_resource_groups_and_members_set(uuid: str, /, instance=None, group=None) -> ResourceGroupsAndMembersSet:
        """
        returns a tuple containing:
         - The "Anonymous" Group
         - The "Registered Members" Group
         - The "Groups" belonging to the Resource Owner
         - The "managers" of the Groups affecting the Resource
         - The "members" of the Groups affecting the Resource
        """
        _resource = instance or AdvancedSecurityWorkflowManager.get_instance(uuid)
        anonymous_group = Group.objects.get(name='anonymous')
        registered_members_group = None
        registered_members_group_name = groups_settings.REGISTERED_MEMBERS_GROUP_NAME
        if getattr(groups_settings, 'AUTO_ASSIGN_REGISTERED_MEMBERS_TO_REGISTERED_MEMBERS_GROUP_NAME', False):
            registered_members_group = Group.objects.get(name=registered_members_group_name)
        user_groups = get_user_groups(_resource.owner, group=group)
        resource_groups, group_managers = _resource.get_group_managers(group=group)

        return ResourceGroupsAndMembersSet(anonymous_group, registered_members_group, user_groups, resource_groups, group_managers)

    @staticmethod
    def get_workflow_permissions(uuid: str, /, instance=None, perm_spec: dict = {"users": {}, "groups": {}}, created: bool = False,
                                 approval_status_changed: bool = False, group_status_changed: bool = False) -> dict:
        """
        Adapts the provided "perm_spec" accordingly to the following schema:
                                | RESOURCE_PUBLISHING | ADMIN_MODERATE_UPLOADS
          --------------------------------------------------------------------
            AUTO PUBLISH        |          X          |           X
            SIMPLE PUBLISHING   |          V          |           X
            SIMPLIFIED WORKFLOW |          X          |           V
            ADVANCED WORKFLOW   |          V          |           V

        General Rules:
         - OWNER can never publish, except in the AUTO_PUBLISHING workflow
         - MANAGERS can always "publish" the resource
         - MEMBERS can always "view" and "download" the resource
         - When the OWNER is also a MANAGER, the MANAGER wins! Therefore he can publish too
         - Others, except in the AUTO_PUBLISHING workflow

                              |  N/PUBLISHED   | PUBLISHED
            ----------------------------------------------
                N/APPROVED    |     GM/OWR     |     -
                APPROVED      |   registerd    |    all
            ----------------------------------------------
          - There are few exceptions accordingly to the enabled workflow
            * SIMPLIFIED WORKFLOW: If the resource will be "approved" or "published" the OWNERS won't be able change the resource data and perms
            * ADVANCED WORKFLOW: If the resource will be "approved" or "published" the OWNERS won't be able change the resource data, metadata and perms
        """
        _resource = instance or AdvancedSecurityWorkflowManager.get_instance(uuid)
        _perm_spec = copy.deepcopy(perm_spec)

        def safe_remove(perms, perm): perms.remove(perm) if perm in perms else None

        if _resource:
            _resource = _resource.get_real_instance()

            AdminViewPermissionsSet = AdvancedSecurityWorkflowManager.compute_admin_and_view_permissions_set(uuid, instance=_resource)
            ResourceGroupsAndMembersSet = AdvancedSecurityWorkflowManager.compute_resource_groups_and_members_set(uuid, instance=_resource, group=_resource.group)

            # Computing the OWNER Permissions
            prev_perms = _perm_spec['users'].get(_resource.owner, []) if isinstance(_perm_spec['users'], dict) else []
            prev_perms += AdminViewPermissionsSet.view_perms.copy() + AdminViewPermissionsSet.admin_perms.copy()
            prev_perms = list(set(prev_perms))
            if not AdvancedSecurityWorkflowManager.is_auto_publishing_workflow():
                # Check if owner is a manager of any group and add admin_manager_perms accordingly
                if _resource.owner not in ResourceGroupsAndMembersSet.managers:
                    safe_remove(prev_perms, 'publish_resourcebase')
                    if not AdvancedSecurityWorkflowManager.is_simple_publishing_workflow() and (_resource.is_approved or _resource.is_published):
                        safe_remove(prev_perms, 'change_resourcebase')
                        safe_remove(prev_perms, 'change_resourcebase_metadata')
                    if AdvancedSecurityWorkflowManager.is_advanced_workflow():
                        safe_remove(prev_perms, 'change_resourcebase_permissions')
            _perm_spec['users'][_resource.owner] = list(set(prev_perms))

            # Computing the MANAGERs and MEMBERs Permissions
            if not AdvancedSecurityWorkflowManager.is_auto_publishing_workflow():
                if group_status_changed:
                    # Reset Groups/Manager Perms
                    _owner_perms = copy.deepcopy(_perm_spec['users'].get(_resource.owner, []))
                    _perm_spec['users'] = {_resource.owner: _owner_perms}
                    _perm_spec['groups'] = {}

                if ResourceGroupsAndMembersSet.managers:
                    for user in ResourceGroupsAndMembersSet.managers:
                        prev_perms = _perm_spec["users"].get(user, []) if "users" in _perm_spec else []
                        prev_perms += AdminViewPermissionsSet.view_perms.copy() + AdminViewPermissionsSet.admin_perms.copy()
                        prev_perms = list(set(prev_perms))
                        _perm_spec["users"][user] = list(set(prev_perms))

                if ResourceGroupsAndMembersSet.resource_groups:
                    for group in ResourceGroupsAndMembersSet.resource_groups:
                        prev_perms = _perm_spec["groups"].get(group, []) if "groups" in _perm_spec else []
                        prev_perms += AdminViewPermissionsSet.view_perms.copy()
                        prev_perms = list(set(prev_perms))
                        _perm_spec["groups"][group] = list(set(prev_perms))
                elif len(_perm_spec["groups"]):
                    groups = copy.deepcopy(_perm_spec["groups"])
                    for group in groups:
                        if group not in (ResourceGroupsAndMembersSet.anonymous_group, ResourceGroupsAndMembersSet.registered_members_group):
                            try:
                                group = group if hasattr(group, 'group') else GroupProfile.objects.get(group=group)
                                users = list(group.get_managers()) + list(group.get_members())
                                for user in users:
                                    if _perm_spec["users"].get(user, None):
                                        _perm_spec["users"].pop(user)
                                if _perm_spec["groups"].get(group.group, None):
                                    _perm_spec["groups"].pop(group.group)
                            except Exception as e:
                                logger.exception(e)

            # Computing the 'All Others' Permissions
            if ResourceGroupsAndMembersSet.anonymous_group:
                prev_perms = _perm_spec['groups'].get(ResourceGroupsAndMembersSet.anonymous_group, []) if isinstance(_perm_spec['groups'], dict) else []
                if approval_status_changed and (_resource.is_approved or _resource.is_published):
                    prev_perms += AdminViewPermissionsSet.view_perms.copy()
                    prev_perms = list(set(prev_perms))
                if created:
                    if not AdvancedSecurityWorkflowManager.is_anonymous_can_view():
                        safe_remove(prev_perms, 'view_resourcebase')
                    if not AdvancedSecurityWorkflowManager.is_anonymous_can_download():
                        safe_remove(prev_perms, 'download_resourcebase')
                if not AdvancedSecurityWorkflowManager.is_auto_publishing_workflow():
                    if ((AdvancedSecurityWorkflowManager.is_simple_publishing_workflow() or AdvancedSecurityWorkflowManager.is_advanced_workflow()) and not _resource.is_published) or (
                            AdvancedSecurityWorkflowManager.is_simplified_workflow() and not (_resource.is_approved or _resource.is_published)):
                        safe_remove(prev_perms, 'view_resourcebase')
                        safe_remove(prev_perms, 'download_resourcebase')
            _perm_spec['groups'][ResourceGroupsAndMembersSet.anonymous_group] = list(set(prev_perms))

            if ResourceGroupsAndMembersSet.registered_members_group and getattr(groups_settings, 'AUTO_ASSIGN_REGISTERED_MEMBERS_TO_REGISTERED_MEMBERS_GROUP_NAME', False):
                prev_perms = _perm_spec['groups'].get(ResourceGroupsAndMembersSet.registered_members_group, []) if isinstance(_perm_spec['groups'], dict) else []
                if approval_status_changed and (_resource.is_approved or _resource.is_published):
                    prev_perms += AdminViewPermissionsSet.view_perms.copy()
                    prev_perms = list(set(prev_perms))
                if not AdvancedSecurityWorkflowManager.is_auto_publishing_workflow() and not _resource.is_approved:
                    safe_remove(prev_perms, 'view_resourcebase')
                    safe_remove(prev_perms, 'download_resourcebase')
                _perm_spec['groups'][ResourceGroupsAndMembersSet.registered_members_group] = list(set(prev_perms))

        return _perm_spec

    @staticmethod
    def get_permissions(uuid: str, /, instance=None, permissions: dict = {}, created: bool = False,
                        approval_status_changed: bool = False, group_status_changed: bool = False) -> dict:
        """
          Fix-ups the perm_spec accordingly to the enabled workflow (if any).
          For more details check the "get_workflow_permissions" method
        """
        _resource = instance or AdvancedSecurityWorkflowManager.get_instance(uuid)

        _permissions = None
        if permissions:
            if PermSpecCompact.validate(permissions):
                _permissions = PermSpecCompact(copy.deepcopy(permissions), _resource).extended
            else:
                _permissions = copy.deepcopy(permissions)

        if _resource:
            perm_spec = _permissions or copy.deepcopy(_resource.get_all_level_info())

            # Sanity checks
            if isinstance(perm_spec, str):
                perm_spec = json.loads(perm_spec)

            if "users" not in perm_spec:
                perm_spec["users"] = {}
            elif isinstance(perm_spec["users"], list):
                _users = {}
                for _item in perm_spec["users"]:
                    _users[_item[0]] = _item[1]
                perm_spec["users"] = _users

            if "groups" not in perm_spec:
                perm_spec["groups"] = {}
            elif isinstance(perm_spec["groups"], list):
                _groups = {}
                for _item in perm_spec["groups"]:
                    _groups[_item[0]] = _item[1]
                perm_spec["groups"] = _groups

            # Make sure we're dealing with "Profile"s and "Group"s...
            perm_spec = _resource.fixup_perms(perm_spec)
            perm_spec = AdvancedSecurityWorkflowManager.get_workflow_permissions(
                _resource.uuid, instance=_resource, perm_spec=perm_spec, created=created,
                approval_status_changed=approval_status_changed, group_status_changed=group_status_changed)

        return perm_spec

    @staticmethod
    def handle_moderated_uploads(uuid: str, /, instance=None) -> object:
        _resource = instance or AdvancedSecurityWorkflowManager.get_instance(uuid)

        if _resource:
            if not AdvancedSecurityWorkflowManager.is_auto_publishing_workflow():
                _resource.is_approved = False
                _resource.was_approved = False
                _resource.is_published = False
                _resource.was_published = False

                from geonode.base.models import ResourceBase
                ResourceBase.objects.filter(
                    uuid=_resource.uuid).update(
                        is_approved=False, was_approved=False,
                        is_published=False, was_published=False)

        return _resource

    @staticmethod
    def set_group_member_permissions(user, group, role):

        if not AdvancedSecurityWorkflowManager.is_auto_publishing_workflow():
            '''
            Internally the set_permissions function will automatically handle the permissions
            that needs to be assigned to re resource.
            Background at: https://github.com/GeoNode/geonode/pull/8145
            If the user is demoted, we assign by default at least the view and the download permission
            to the resource
            '''
            queryset = (
                get_objects_for_user(
                    user,
                    ["base.view_resourcebase", "base.change_resourcebase"],
                    any_perm=True)
                .filter(group=group.group)
                .exclude(owner=user)
            )
            # A.F.: By including 'group.resources()' here, we will look also for resources
            #       having permissions related to the current 'group' and not only the ones assigned
            #       to the 'group' through the metadata settings.
            _resources = set([_r for _r in queryset.iterator()] + [_r for _r in group.resources()])
            if len(_resources) == 0:
                queryset = (
                    get_objects_for_user(
                        user,
                        ["base.view_resourcebase", "base.change_resourcebase"],
                        any_perm=True)
                    .filter(owner=user)
                )
                _resources = queryset.iterator()
            for _r in _resources:
                perm_spec = _r.get_all_level_info()
                if "users" not in perm_spec:
                    perm_spec["users"] = {}
                if "groups" not in perm_spec:
                    perm_spec["groups"] = {}

                AdminViewPermissionsSet = AdvancedSecurityWorkflowManager.compute_admin_and_view_permissions_set(_r.uuid, instance=_r)

                prev_perms = AdminViewPermissionsSet.view_perms.copy()
                if not role:
                    prev_perms = []
                    if user == _r.owner:
                        _group = group if hasattr(group, 'group') else GroupProfile.objects.get(group=group)
                        _users = list(_group.get_managers()) + list(_group.get_members())
                        for _m in _users:
                            if perm_spec["users"].get(_m, None):
                                perm_spec["users"].pop(_m)

                        if perm_spec["groups"].get(_group.group, None):
                            perm_spec["groups"].pop(_group.group)
                elif role == "manager":
                    prev_perms += AdminViewPermissionsSet.admin_perms.copy()
                    prev_perms = list(set(prev_perms))
                perm_spec["users"][user] = list(set(prev_perms))

                # Let's the ResourceManager finally decide which are the correct security settings to apply
                _r.set_permissions(perm_spec)
