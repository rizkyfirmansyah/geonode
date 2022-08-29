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
import logging
import traceback
import warnings
import pandas as pd
import os
from django.db.models import Max

import numpy as np
from django.views.decorators.csrf import csrf_exempt

from geonode.decorators import registered_users
from geonode.datasets.tasks import delete_orphaned_thumbnail
from geonode.favorite.models import Favorite
from geonode.notifications_helper import toast_unauthorized
from geonode.views import page_not_found_message, unauthorized_message

from guardian.shortcuts import get_objects_for_user
from django.shortcuts import render, redirect, get_object_or_404
from django.template import loader
from django.http import HttpResponse, HttpResponseRedirect
from django.utils.translation import ugettext as _
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.urls import reverse
from django.core.exceptions import PermissionDenied, ObjectDoesNotExist
from django.views.generic.edit import CreateView
from django.db.models import F
from django.forms.utils import ErrorList
from django.views.decorators.http import require_POST
from django.contrib.auth.mixins import LoginRequiredMixin
from geonode.base.api.exceptions import geonode_exception_handler

from geonode.datasets.utils import get_download_response
from geonode.utils import resolve_object
from geonode.security.views import _perms_info_json
from geonode.people.forms import ProfileForm
from geonode.base.auth import get_or_create_token
from geonode.base.forms import CategoryForm, RegionsForm, TKeywordForm, ThesaurusAvailableForm
from geonode.base.models import (
    ResourceBase,
    Thesaurus)
from geonode.datasets.enumerations import DATASET_TYPE_MAP, DOCUMENT_MIMETYPE_MAP
from geonode.datasets.models import Dataset, File
from geonode.resource.utils import get_related_resources
from geonode.datasets.forms import DatasetForm, DatasetCreateForm, DatasetReplaceForm
from geonode.utils import build_social_links
from geonode.groups.models import GroupProfile
from geonode.base.views import batch_modify, batch_permissions
from geonode.base import register_event
from geonode.monitoring.models import EventType
from geonode.security.utils import get_user_visible_groups, get_visible_resources, sha256sum
from django.contrib import messages
import uuid

from dal import autocomplete

logger = logging.getLogger("geonode.datasets.views")

ALLOWED_DOC_TYPES = settings.ALLOWED_DOCUMENT_TYPES

_PERMISSION_MSG_DELETE = _("You are not permitted to delete this dataset")
_PERMISSION_MSG_GENERIC = _("You do not have permissions for this dataset.")
_PERMISSION_MSG_MODIFY = _("You are not permitted to modify this dataset.")
_PERMISSION_MSG_METADATA = _("You are not permitted to modify this dataset's metadata.")
_PERMISSION_MSG_VIEW = _("You are not permitted to view this dataset.")


def _resolve_dataset(request, docid, permission='base.change_resourcebase',
                      msg=_PERMISSION_MSG_GENERIC, **kwargs):
    '''
    Resolve the dataset by the provided primary key and check the optional permission.
    '''
    return resolve_object(request, Dataset, {'pk': docid},
                          permission=permission, permission_msg=msg, **kwargs)


@registered_users
def dataset_detail(request, docid):
    """
    The view that show details of each dataset
    """
    try:
        dataset =_resolve_dataset(
            request,
            docid,
            'base.view_resourcebase',
            _PERMISSION_MSG_VIEW)

    except PermissionDenied:
        return unauthorized_message(request, _PERMISSION_MSG_VIEW)

    except Exception:
        return page_not_found_message(request)

    if not dataset:
        return page_not_found_message(request)

    # Add metadata_author or poc if missing
    dataset.add_missing_metadata_author_or_poc()

    related = get_related_resources(dataset)
    files = File.objects.filter(dataset_id__in=[dataset.id])
    # Update count for popularity ranking,
    # but do not includes admins or resource owners
    if request.user != dataset.owner and not request.user.is_superuser:
        Dataset.objects.filter(
            id=dataset.id).update(
            popular_count=F('popular_count') + 1)

    metadata = dataset.link_set.metadata().filter(
        name__in=settings.DOWNLOAD_FORMATS_METADATA)

    try:
        is_favorited = Favorite.objects.filter(user=request.user, object_id=dataset.pk).exists()
    except Favorite.DoesNotExist:
        is_favorited = False

    # Call this first in order to be sure "perms_list" is correct
    permissions_json = _perms_info_json(dataset)

    perms_list = list(
        dataset.get_self_resource().get_user_perms(request.user)
        .union(dataset.get_user_perms(request.user))
    )

    group = None
    if dataset.group:
        try:
            group = GroupProfile.objects.get(slug=dataset.group.name)
        except ObjectDoesNotExist:
            group = None

    access_token = None
    if request and request.user:
        access_token = get_or_create_token(request.user)
        if access_token and not access_token.is_expired():
            access_token = access_token.token
        else:
            access_token = None

    AUDIOTYPES = [_e for _e, _t in DATASET_TYPE_MAP.items() if _t == 'audio']
    IMGTYPES = [_e for _e, _t in DATASET_TYPE_MAP.items() if _t == 'image']
    VIDEOTYPES = [_e for _e, _t in DATASET_TYPE_MAP.items() if _t == 'video']
    WORDTYPES = [_e for _e, _t in DATASET_TYPE_MAP.items() if _t == 'word']
    EXCELTYPES = [_e for _e, _t in DATASET_TYPE_MAP.items() if _t == 'excel']
    PPTTYPES = [_e for _e, _t in DATASET_TYPE_MAP.items() if _t == 'powerpoint']
    TABULARTYPES = [_e for _e, _t in DATASET_TYPE_MAP.items() if _t == 'tabular']

    context_dict = {
        'access_token': access_token,
        'resource': dataset,
        'files': files,
        'perms_list': perms_list,
        'permissions_json': permissions_json,
        'group': group,
        'metadata': metadata,
        'is_favorited': is_favorited,
        'audiotypes': AUDIOTYPES,
        'imgtypes': IMGTYPES,
        'videotypes': VIDEOTYPES,
        'wordtypes': WORDTYPES,
        'exceltypes': EXCELTYPES,
        'ppttypes': PPTTYPES,
        'tabulartypes': TABULARTYPES,
        'mimetypemap': DOCUMENT_MIMETYPE_MAP,
        'related': related}

    if settings.SOCIAL_ORIGINS:
        context_dict["social_links"] = build_social_links(
            request, dataset)

    if getattr(settings, 'EXIF_ENABLED', False):
        try:
            from geonode.datasets.exif.utils import exif_extract_dict
            exif = exif_extract_dict(dataset)
            if exif:
                context_dict['exif_data'] = exif
        except Exception:
            logger.error("Exif extraction failed.")

    if request.user.is_authenticated:
        if getattr(settings, 'FAVORITE_ENABLED', False):
            from geonode.favorite.utils import get_favorite_info
            context_dict["favorite_info"] = get_favorite_info(request.user, dataset)

    register_event(request, EventType.EVENT_VIEW, dataset)

    return render(
        request,
        "datasets/dataset_detail.html",
        context=context_dict)


def dataset_download(request, docid):
    response = get_download_response(request, docid, attachment=True)
    return response


def dataset_link(request, docid):
    response = get_download_response(request, docid)
    return response

def dataset_embed(request, docid):
    from django.http.response import HttpResponseRedirect
    dataset =get_object_or_404(File, pk=docid)

    if not request.user.has_perm(
            'base.download_resourcebase',
            obj=dataset.get_self_resource()):
        return HttpResponse(
            loader.render_to_string(
                'error/401.html', context={
                    'error_message': _("You are not allowed to view this dataset.")}, request=request), status=401)
    if dataset.is_image:
        if dataset.doc_url:
            imageurl = dataset.doc_url
        else:
            imageurl = reverse('dataset_link', args=(dataset.id,))
        context_dict = {
            "image_url": imageurl,
            "resource": dataset.get_self_resource(),
        }
        return render(
            request,
            "datasets/dataset_embed.html",
            context_dict
        )
    if dataset.doc_url:
        return HttpResponseRedirect(dataset.doc_url)
    else:
        context_dict = {
            "dataset_link": reverse('dataset_link', args=(dataset.id,)),
            "resource": dataset.get_self_resource(),
        }
        return render(
            request,
            "datasets/dataset_embed.html",
            context_dict
        )


class DatasetUploadView(LoginRequiredMixin, CreateView):
    template_name = 'datasets/dataset_upload.html'
    form_class = DatasetCreateForm
    context_object_name = 'dataset'

    def post(self, request, *args, **kwargs):
        self.object = None
        try:
            return super().post(request, *args, **kwargs)
        except Exception as e:
            exception_response = geonode_exception_handler(e, {})
            return HttpResponse(
                json.dumps(exception_response.data),
                content_type='application/json',
                status=exception_response.status_code)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        import_id = list(File.objects.all().aggregate(Max('import_id')).values())[0]
        import_id = (int(import_id) + 1) if import_id is not None else 0
        TABULARTYPES = [_e for _e, _t in DATASET_TYPE_MAP.items() if _t == 'tabular']
        context["ALLOWED_DOC_TYPES"] = ALLOWED_DOC_TYPES
        context["TABULARTYPES"] = TABULARTYPES
        context["import_id"] = import_id
        self.request.session['session'] =  str(uuid.uuid1())

        return context


class DatasetUpdateView(LoginRequiredMixin, CreateView):
    template_name = 'datasets/dataset_replace.html'
    form_class = DatasetReplaceForm
    queryset = Dataset.objects.all()
    context_object_name = 'dataset'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        import_id = list(File.objects.all().aggregate(Max('import_id')).values())[0]
        import_id = (int(import_id) + 1) if import_id is not None else 0
        context["import_id"] = import_id
        self.request.session['session'] =  str(uuid.uuid1())
        context['ALLOWED_DOC_TYPES'] = ALLOWED_DOC_TYPES
        pk_url_kwarg = self.kwargs['docid']
        context['dataset_id'] = pk_url_kwarg
        files = File.objects.filter(dataset_id__in=[pk_url_kwarg])
        context['files'] = files

        return context
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superuser and not request.user.has_perm('change_resourcebase'):
            return unauthorized_message(request, _PERMISSION_MSG_MODIFY)

        return super().dispatch(request, *args, **kwargs)


def dataset_metadata(
        request,
        docid,
        template='datasets/dataset_metadata.html',
        ajax=True):
    dataset =None
    try:
        dataset =_resolve_dataset(
            request,
            docid,
            'base.change_resourcebase_metadata',
            _PERMISSION_MSG_METADATA)
    except PermissionDenied:
        return unauthorized_message(request, _PERMISSION_MSG_VIEW)

    except Exception:
        return page_not_found_message(request)

    if not dataset:
        return page_not_found_message(request)

    # Add metadata_author or poc if missing
    dataset.add_missing_metadata_author_or_poc()
    poc = dataset.poc
    metadata_author = dataset.metadata_author
    topic_category = dataset.category.all()

    if request.method == "POST":
        dataset_form = DatasetForm(
            request.POST,
            instance=dataset,
            prefix="resource")
        category_form = CategoryForm(request.POST, prefix="category_choice_field",
                    initial=(
                        request.POST.getlist("category_choice_field") if "category_choice_field" in request.POST or
                        request.POST.getlist("category_choice_field") else []))
        region_form = RegionsForm(request.POST, prefix="resource-regions",
                    initial=(
                        request.POST.getlist("resource-regions") if "resource-regions" in request.POST or
                        request.POST.getlist("resource-regions") else []))
        if hasattr(settings, 'THESAURUS'):
            tkeywords_form = TKeywordForm(request.POST)
        else:
            tkeywords_form = ThesaurusAvailableForm(request.POST, prefix='tkeywords')

        if dataset_form.is_valid() and tkeywords_form.is_valid():
            new_poc = dataset_form.cleaned_data['poc']
            new_author = dataset_form.cleaned_data['metadata_author']
            new_keywords = dataset_form.cleaned_data['keywords']
            new_regions = [int(c.strip()) for c in request.POST.getlist('resource-regions')]
            new_categories = [int(c.strip()) for c in request.POST.getlist('category_choice_field')]

            if new_poc is None:
                if poc is None:
                    poc_form = ProfileForm(
                        request.POST,
                        prefix="poc",
                        instance=poc)
                else:
                    poc_form = ProfileForm(request.POST, prefix="poc")
                if poc_form.is_valid():
                    if len(request.POST['profile']) == 0:
                        # FIXME use form.add_error in django > 1.7
                        errors = poc_form._errors.setdefault(
                            'profile', ErrorList())
                        errors.append(
                            _('You must set a point of contact for this resource'))
                if poc_form.has_changed and poc_form.is_valid():
                    new_poc = poc_form.save()

            if new_author is None:
                if metadata_author is None:
                    author_form = ProfileForm(request.POST, prefix="author", instance=metadata_author)
                else:
                    author_form = ProfileForm(request.POST, prefix="author")
                if author_form.is_valid():
                    if len(request.POST['profile']) == 0:
                        # FIXME use form.add_error in django > 1.7
                        errors = author_form._errors.setdefault(
                            'profile', ErrorList())
                        errors.append(
                            _('You must set an author for this resource'))
                if author_form.has_changed and author_form.is_valid():
                    new_author = author_form.save()

            dataset =dataset_form.instance
            if new_poc is not None and new_author is not None:
                dataset.poc = new_poc
                dataset.metadata_author = new_author
            dataset.keywords.clear()
            dataset.keywords.add(*new_keywords)
            dataset.regions.clear()
            dataset.regions.add(*new_regions)
            dataset.category.clear()
            dataset.category.add(*new_categories)
            dataset.save(notify=True)
            dataset_form.save_many2many()

            register_event(request, EventType.EVENT_CHANGE_METADATA, dataset)
            if not ajax:
                return HttpResponseRedirect(
                    reverse(
                        'dataset_detail',
                        args=(
                            dataset.id,
                        )))

            try:
                # Keywords from THESAURUS management
                # Rewritten to work with updated autocomplete
                if not tkeywords_form.is_valid():
                    return HttpResponse(json.dumps({'message': "Invalid thesaurus keywords"}, status_code=400))

                thesaurus_setting = getattr(settings, 'THESAURUS', None)
                if thesaurus_setting:
                    tkeywords_data = tkeywords_form.cleaned_data['tkeywords']
                    tkeywords_data = tkeywords_data.filter(
                        thesaurus__identifier=thesaurus_setting['name']
                    )
                    dataset.tkeywords.set(tkeywords_data)
                elif Thesaurus.objects.all().exists():
                    fields = tkeywords_form.cleaned_data
                    dataset.tkeywords.set(tkeywords_form.cleanx(fields))

            except Exception:
                tb = traceback.format_exc()
                logger.error(tb)

            toast_title = _("Update Metadata")
            message = _("Metadata {} has been updated".format(dataset.title))
            messages.success(request, message, extra_tags=toast_title)

            return HttpResponse(json.dumps({'message': "Metadata has been updated"}))

    else:
        dataset_form = DatasetForm(instance=dataset, prefix="resource")
        dataset_form.disable_keywords_widget_for_non_superuser(request.user)
        #  set initial values for category form
        ids = list(c.id for c in topic_category)
        category_form = CategoryForm(
                    prefix="category_choice_field",
                    initial=ids)
        region_list = list(r.id for r in dataset.regions.all())
        region_form = RegionsForm(
                    prefix="region_choice_field",
                    initial=region_list)

        # Keywords from THESAURUS management
        doc_tkeywords = dataset.tkeywords.all()
        if hasattr(settings, 'THESAURUS') and settings.THESAURUS:
            warnings.warn('The settings for Thesaurus has been moved to Model, \
            this feature will be removed in next releases', DeprecationWarning)
            tkeywords_list = ''
            lang = 'en'  # TODO: use user's language
            if doc_tkeywords and len(doc_tkeywords) > 0:
                tkeywords_ids = doc_tkeywords.values_list('id', flat=True)
                if hasattr(settings, 'THESAURUS') and settings.THESAURUS:
                    el = settings.THESAURUS
                    thesaurus_name = el['name']
                    try:
                        t = Thesaurus.objects.get(identifier=thesaurus_name)
                        for tk in t.thesaurus.filter(pk__in=tkeywords_ids):
                            tkl = tk.keyword.filter(lang=lang)
                            if len(tkl) > 0:
                                tkl_ids = ",".join(
                                    map(str, tkl.values_list('id', flat=True)))
                                tkeywords_list += "," + \
                                tkl_ids if len(
                                    tkeywords_list) > 0 else tkl_ids
                    except Exception:
                        tb = traceback.format_exc()
                        logger.error(tb)

            tkeywords_form = TKeywordForm(instance=dataset)
        else:
            tkeywords_form = ThesaurusAvailableForm(prefix='tkeywords')
            #  set initial values for thesaurus form
            for tid in tkeywords_form.fields:
                values = []
                values = [keyword.id for keyword in doc_tkeywords if int(tid) == keyword.thesaurus.id]
                tkeywords_form.fields[tid].initial = values

    # Request.GET
    if poc is not None:
        dataset_form.fields['poc'].initial = poc.id
        poc_form = ProfileForm(prefix="poc")
        poc_form.hidden = True

    if metadata_author is not None:
        dataset_form.fields['metadata_author'].initial = metadata_author.id
        author_form = ProfileForm(prefix="author")
        author_form.hidden = True

    metadata_author_groups = get_user_visible_groups(request.user)

    if settings.ADMIN_MODERATE_UPLOADS:
        if not request.user.is_superuser:
            can_change_metadata = request.user.has_perm(
                'change_resourcebase_metadata',
                dataset.get_self_resource())
            try:
                is_manager = request.user.groupmember_set.all().filter(role='manager').exists()
            except Exception:
                is_manager = False
            if not is_manager or not can_change_metadata:
                if settings.RESOURCE_PUBLISHING:
                    dataset_form.fields['is_published'].widget.attrs.update(
                        {'disabled': 'true'})
                dataset_form.fields['is_approved'].widget.attrs.update(
                    {'disabled': 'true'})

    register_event(request, EventType.EVENT_VIEW_METADATA, dataset)
    return render(request, template, context={
        "resource": dataset,
        "dataset": dataset,
        "dataset_form": dataset_form,
        "poc_form": poc_form,
        "author_form": author_form,
        "category_form": category_form,
        "region_form": region_form,
        "tkeywords_form": tkeywords_form,
        "metadata_author_groups": metadata_author_groups,
        "TOPICCATEGORY_MANDATORY": getattr(settings, 'TOPICCATEGORY_MANDATORY', False),
        "GROUP_MANDATORY_RESOURCES": getattr(settings, 'GROUP_MANDATORY_RESOURCES', False),
        "UI_MANDATORY_FIELDS": list(
            set(getattr(settings, 'UI_DEFAULT_MANDATORY_FIELDS', []))
            |
            set(getattr(settings, 'UI_REQUIRED_FIELDS', []))
        )
    })


@login_required
def dataset_metadata_advanced(request, docid):
    return dataset_metadata(
        request,
        docid,
        template='datasets/dataset_metadata_advanced.html')


@login_required
@require_POST
def dataset_remove(request):
    docid = request.POST['docid']
    try:
        dataset =_resolve_dataset(
            request,
            docid,
            'base.delete_resourcebase',
            _PERMISSION_MSG_DELETE)
        logger.debug(f'Deleting File {dataset}')
        # delete_orphaned_thumbnail.apply((dataset.thumbnail_path,))
        dataset.delete()
        message = _("File: {} has been deleted".format(dataset.title))
        register_event(request, EventType.EVENT_REMOVE, dataset)
        messages.error(request, message, extra_tags=_PERMISSION_MSG_DELETE)

        return redirect('catalogue_browse')

    except PermissionDenied:
        return unauthorized_message(request, _PERMISSION_MSG_DELETE)

    except Exception:
        traceback.print_exc()
        message = f'{_("We are incredibly sorry, we could not execute to delete")}: {dataset.title}.'
        message += f'{_("Please submit a ticket or fill the form in the help & support. Thank you.")}'

        messages.error(request, message, extra_tags=_PERMISSION_MSG_DELETE)

        return redirect('catalogue_browse')


@registered_users
def dataset_metadata_detail(
        request,
        docid,
        template='datasets/dataset_metadata_detail.html'):
    try:
        dataset =_resolve_dataset(
            request,
            docid,
            'view_resourcebase',
            _PERMISSION_MSG_METADATA)
    except PermissionDenied:
        return unauthorized_message(request, _PERMISSION_MSG_VIEW)

    except Exception:
        return page_not_found_message(request)

    if not dataset:
        return page_not_found_message(request)

    group = None
    if dataset.group:
        try:
            group = GroupProfile.objects.get(slug=dataset.group.name)
        except ObjectDoesNotExist:
            group = None
    site_url = settings.SITEURL.rstrip('/') if settings.SITEURL.startswith('http') else settings.SITEURL
    register_event(request, EventType.EVENT_VIEW_METADATA, dataset)
    return render(request, template, context={
        "resource": dataset,
        "group": group,
        'SITEURL': site_url
    })


@login_required
def dataset_batch_metadata(request):
    return batch_modify(request, 'File')


@login_required
def dataset_batch_permissions(request):
    return batch_permissions(request, 'File')


class DatasetAutocomplete(autocomplete.Select2QuerySetView):

    def get_queryset(self):
        request = self.request
        permitted = get_objects_for_user(
            request.user,
            'base.view_resourcebase')
        qs = File.objects.all().filter(id__in=permitted)

        if self.q:
            qs = qs.filter(title__icontains=self.q)

        return get_visible_resources(
            qs,
            request.user if request else None,
            admin_approval_required=settings.ADMIN_MODERATE_UPLOADS,
            unpublished_not_visible=settings.RESOURCE_PUBLISHING,
            private_groups_not_visibile=settings.GROUP_PRIVATE_RESOURCES)


@csrf_exempt
@login_required
def render_tabular(request, docid):
      """
      Read tabular files directly from files and return as html
      """
      try:
          dataset =_resolve_dataset(
              request,
              docid,
              'base.view_resourcebase',
            _PERMISSION_MSG_VIEW)
      except PermissionDenied:
          return unauthorized_message(request, _PERMISSION_MSG_VIEW)

      def replace_nan(df):
          # replace all NaNs with an empty string
          df = df.replace(np.nan, '', regex=True)
          return df
      
      if dataset.files:
          tabular = [os.path.basename(f) for f in dataset.files][0]
          data = os.path.join(settings.MEDIA_ROOT, settings.dataset_LOCATION, 'tabular', tabular)
          if dataset.extension == 'csv':
              df = pd.read_csv(data)
              df = df.head(200)
              replace_nan(df)

          elif dataset.extension == 'tsv':
              df = pd.read_csv(data, sep='\t', header=0)
              df = df.head(200)
              replace_nan(df)

          elif dataset.extension == 'sav':
              df = pd.read_spss(data)
              df = df.head(200)
              replace_nan(df)

          elif dataset.extension == 'dta':
              ## need to find other methods to read efficiently
              stata = pd.read_stata(data, chunksize=5000)
              df = pd.DataFrame()
              for i in stata:
                  df = df.append(i)
              
              replace_nan(df)

      classes = 'table table-sm'
      render_df = df.to_html(classes=classes, justify='center', table_id='tabular_data')      
      
      return HttpResponse(render_df)