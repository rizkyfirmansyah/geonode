# -*- coding: utf-8 -*-
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
import json
from django.contrib import messages

from django import forms
from django.apps import apps
from django.db.models import Q
from django.urls import reverse
from django.conf import settings
from django.shortcuts import render_to_response, render
from django.template.response import TemplateResponse
from geonode.base.templatetags.base_tags import facets
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth import authenticate, login, get_user_model

from geonode import get_version
from geonode.groups.models import GroupProfile
from geonode.geoapps.models import GeoApp
from django.utils.translation import ugettext as _

import logging
logger = logging.getLogger(__name__)


class AjaxLoginForm(forms.Form):
    password = forms.CharField(widget=forms.PasswordInput)
    username = forms.CharField()


def ajax_login(request):
    if request.method != 'POST':
        return HttpResponse(
            content="ajax login requires HTTP POST",
            status=405,
            content_type="text/plain"
        )

    form = AjaxLoginForm(request.POST)
    logger.info(f'FORM LOGIN: {form}')
    if form.is_valid():
        username = form.cleaned_data['username']
        password = form.cleaned_data['password']
        user = authenticate(username=username, password=password)
        if user is None or not user.is_active:
            return HttpResponse(
                content="bad credentials or disabled user",
                status=400,
                content_type="text/plain"
            )
        else:
            login(request, user)
            if request.session.test_cookie_worked():
                request.session.delete_test_cookie()
            return HttpResponse(
                content="successful login",
                status=200,
                content_type="text/plain"
            )
    else:
        return HttpResponse(
            "The form you submitted doesn't look like a username/password combo.",
            content_type="text/plain",
            status=400)


def ajax_lookup(request):
    if request.method != 'POST':
        return HttpResponse(
            content='ajax user lookup requires HTTP POST',
            status=405,
            content_type='text/plain'
        )
    elif 'query' not in request.POST:
        return HttpResponse(
            content='use a field named "query" to specify a prefix to filter usernames',
            content_type='text/plain')
    keyword = request.POST['query']
    users = get_user_model().objects.filter(
        Q(username__icontains=keyword)).exclude(Q(username='AnonymousUser') |
                                                Q(is_active=False))
    if request.user and request.user.is_authenticated and request.user.is_superuser:
        groups = GroupProfile.objects.filter(
            Q(title__icontains=keyword) |
            Q(slug__icontains=keyword))
    elif request.user.is_anonymous:
        groups = GroupProfile.objects.filter(
            Q(title__icontains=keyword) |
            Q(slug__icontains=keyword)).exclude(Q(access='private'))
    else:
        groups = GroupProfile.objects.filter(
            Q(title__icontains=keyword) |
            Q(slug__icontains=keyword)).exclude(
                Q(access='private') & ~Q(
                    slug__in=request.user.groupmember_set.all().values_list("group__slug", flat=True))
        )
    json_dict = {
        'users': [({'username': u.username}) for u in users],
        'count': users.count(),
    }
    json_dict['groups'] = [({'name': g.slug, 'title': g.title})
                           for g in groups]
    return HttpResponse(
        content=json.dumps(json_dict),
        content_type='text/plain'
    )


def permission_denied_view(request, exception):
    if not request.user.is_authenticated:
        return HttpResponseRedirect(
            f"{reverse('account_login')}?next={request.get_full_path()}")
    else:
        return TemplateResponse(request, 'error/403.html', {}, status=403).render()


def unauthorized_view(request, exception):
    if not request.user.is_authenticated:
        return HttpResponseRedirect(
            f"{reverse('account_login')}?next={request.get_full_path()}")
    else:
        return TemplateResponse(request, 'error/401.html', {}, status=401).render()


def page_not_found_view(request, exception, template_name="error/404.html"):
    response = render_to_response(template_name)
    response.status_code = 404
    return response


def server_error_view(request, template_name="error/500.html"):
    response = render_to_response(template_name)
    response.status_code = 500
    return response


def page_not_found_message(request, template_name="error/404.html"):
    out = {'success': False}
    out['status_code'] = 404
    out['message'] = _("Hey... what are you trying to look for? Nothing is here.")
    
    return render(request, template_name, context=out)


def unauthorized_message(request, message, template_name="error/403.html"):
    out = {'success': False}
    out['status_code'] = 403
    out['message'] = message
    
    return render(request, template_name, context=out)


def toast_unauthorized(request, toast_title, toast_message=None):
    if toast_title is None:
        toast_title = _("We could not process your request")
    if toast_message is None:
        toast_message = _("You don't have any permissions to modify this resource. Please ask to the resource owner.")
    out = {
      'status_code': 403,
      'toast_message': toast_message,
      'toast_title': toast_title,
    }
    return render(request, "toast/_toast.html", context=out)


def toast_server_error(request, toast_title=None, toast_message=None, status_code=None):
    if status_code is None:
        status_code = 500
    if toast_title is None:
        toast_title = _("We could not process your request")
    if toast_message is None:
        toast_message = _("Something went wrong with your request. Please ask nicely to your admin or developer. Submit a ticket through give feedback.")
    out = {
      'status_code': status_code,
      'toast_message': toast_message,
      'toast_title': toast_title,
    }
    return render(request, "toast/_toast.html", context=out)


def toast_message(request, toast_title, toast_message, status_code=None):
    if status_code is None:
        status_code = 200
    message = {
      'title': toast_title,
      'message': toast_message,
    }
    messages.success(request, message)
    print(messages)
    return render(request, "toast/_toast.html")


def ident_json(request):
    site_url = settings.SITEURL.rstrip('/') if settings.SITEURL.startswith('http') else settings.SITEURL
    json_data = {}
    json_data['siteurl'] = site_url
    json_data['name'] = settings.PYCSW['CONFIGURATION']['metadata:main']['identification_title']

    json_data['poc'] = {
        'name': settings.PYCSW['CONFIGURATION']['metadata:main']['contact_name'],
        'email': settings.PYCSW['CONFIGURATION']['metadata:main']['contact_email'],
        'twitter': f'https://twitter.com/{settings.TWITTER_SITE}'
    }

    json_data['version'] = get_version()

    json_data['services'] = {
        'csw': settings.CATALOGUE['default']['URL'],
        'ows': settings.OGC_SERVER['default']['LOCATION']
    }

    json_data['counts'] = facets({'request': request, 'facet_type': 'home'})

    return HttpResponse(content=json.dumps(json_data),
                        content_type='application/json')


def h_keywords(request):
    from geonode.base.models import HierarchicalKeyword as hk
    p_type = request.GET.get('type', None)
    resource_name = request.GET.get('resource_name', None)
    keywords = hk.resource_keywords_tree(request.user, resource_type=p_type, resource_name=resource_name)

    subtypes = []
    if p_type == 'geoapp':
        for label, app in apps.app_configs.items():
            if hasattr(app, 'type') and app.type == 'GEONODE_APP':
                if hasattr(app, 'default_model'):
                    _model = apps.get_model(label, app.default_model)
                    if issubclass(_model, GeoApp):
                        subtypes.append(_model.__name__.lower())

    for _type in subtypes:
        _bulk_tree = hk.resource_keywords_tree(request.user, resource_type=_type, resource_name=resource_name)
        if isinstance(_bulk_tree, list):
            for _elem in _bulk_tree:
                keywords.append(_elem)
        else:
            keywords.append(_bulk_tree)

    return HttpResponse(content=json.dumps(keywords))


def moderator_contacted(request, inactive_user=None):
    """Used when a user signs up."""
    user = get_user_model().objects.get(id=inactive_user)
    return TemplateResponse(
        request,
        template="account/admin_approval_sent.html",
        context={"email": user.email}
    )
