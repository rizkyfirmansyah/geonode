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
import re
import html
import logging
from django.db.models.query import QuerySet
from bootstrap3_datetime.widgets import DateTimePicker
from dal import autocomplete
from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core import validators
from django.db.models import Prefetch, Q
from django.forms import ModelForm, models
from django.forms.fields import MultipleChoiceField
from django.utils.translation import ugettext as _
from modeltranslation.forms import TranslationModelForm
from taggit.forms import TagField
from tinymce.widgets import TinyMCE
from django.contrib.admin.utils import flatten
from geonode.base.enumerations import ALL_LANGUAGES
from geonode.base.models import (CuratedThumbnail, HierarchicalKeyword,
                                 License, Region, ResourceBase, Thesaurus,
                                 ThesaurusKeyword, ThesaurusKeywordLabel, ThesaurusLabel,
                                 TopicCategory)
from geonode.base.widgets import TaggitSelect2Custom
from geonode.documents.models import Document
from geonode.layers.models import Layer
from django.utils.translation import get_language
from .fields import MultiThesauriField

logger = logging.getLogger(__name__)


def get_tree_data():
    def rectree(parent, path):
        children_list_of_tuples = list()
        c = Region.objects.filter(parent=parent)
        for child in c:
            children_list_of_tuples.append(
                tuple((path + parent.name, tuple((child.id, child.name))))
            )
            childrens = rectree(child, parent.name + '/')
            if childrens:
                children_list_of_tuples.extend(childrens)

        return children_list_of_tuples

    data = list()
    try:
        t = Region.objects.filter(Q(level=0) | Q(parent=None))
        for toplevel in t:
            data.append(
                tuple((toplevel.id, toplevel.name))
            )
            childrens = rectree(toplevel, '')
            if childrens:
                data.append(
                    tuple((toplevel.name, childrens))
                )
    except Exception:
        pass

    return tuple(data)


class AdvancedModelChoiceIterator(models.ModelChoiceIterator):
    def choice(self, obj):
        return (
            self.field.prepare_value(obj),
            self.field.label_from_instance(obj),
            obj)



class RegionsMultipleChoiceField(forms.ModelMultipleChoiceField):
    def _get_choices(self):
        if hasattr(self, '_choices'):
            return self._choices
        return AdvancedModelChoiceIterator(self)

    choices = property(_get_choices, MultipleChoiceField._set_choices)

    def label_from_instance(self, obj):
        return '<span class="has-popover" data-container="body" data-toggle="popover" data-placement="top" ' \
                         'data-content="' + obj.name + '" trigger="hover">' + obj.name + '</span>'



class RegionsForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super(RegionsForm, self).__init__(*args, **kwargs)

    region_choice_field = RegionsMultipleChoiceField(
        required=True,
        label='Regions',
        queryset=Region.objects.order_by('lft', 'name')
    )

    def clean(self):
        cleaned_data = self.data
        return cleaned_data

    @staticmethod
    def label_from_instance(obj):
        return obj.id



class CategoryChoiceField(forms.ModelMultipleChoiceField):
    def _get_choices(self):
        if hasattr(self, '_choices'):
            return self._choices

        return AdvancedModelChoiceIterator(self)

    choices = property(_get_choices, MultipleChoiceField._set_choices)

    def label_from_instance(self, obj):
        return '<i class="fa ' + obj.fa_class + ' fa-2x unchecked"></i>' \
                         '<i class="fa ' + obj.fa_class + ' fa-2x checked"></i>' \
                         '<span class="has-popover" data-container="body" data-toggle="popover" data-placement="top" ' \
                         'data-content="' + obj.description + '" trigger="hover">' \
                                                              '<br/><strong>' + obj.gn_description + '</strong></span>'



class CategoryForm(forms.Form):
    category_choice_field = CategoryChoiceField(
        required=True,
        label=f"*{_('Category')}",
        empty_label=None,
        queryset=TopicCategory.objects.filter(
            is_choice=True).extra(
            order_by=['gn_description']))

    def clean(self):
        cleaned_data = self.data
        ccf_data = cleaned_data.get("category_choice_field")
        category_mandatory = getattr(settings, 'TOPICCATEGORY_MANDATORY', False)
        if category_mandatory and not ccf_data:
            msg = _("Category is required.")
            self._errors = self.error_class([msg])

        # Always return the full collection of cleaned data.
        return cleaned_data

    @staticmethod
    def label_from_instance(obj):
        return obj.id



class TKeywordForm(forms.ModelForm):
    prefix = 'tkeywords'
    class Meta:
        model = Document
        fields = ['tkeywords']

    tkeywords = MultiThesauriField(
        queryset=ThesaurusKeyword.objects.prefetch_related(
            Prefetch('keyword', queryset=ThesaurusKeywordLabel.objects.filter(lang='en'))
        ),
        widget=autocomplete.ModelSelect2Multiple(
            url='thesaurus_autocomplete',
        ),
        label=_("Keywords from Thesaurus"),
        required=False,
        help_text=_("List of keywords from Thesaurus", ),
    )



class ThesaurusAvailableForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super(ThesaurusAvailableForm, self).__init__(*args, **kwargs)
        lang = get_language()
        for item in Thesaurus.objects.all():
            tname = self._get_thesauro_title_label(item, lang)
            if item.card_max == 0:
                continue
            elif item.card_max == 1 and item.card_min == 0:
                self.fields[f"{item.id}"] = self._define_choicefield(item, False, tname, lang)
            elif item.card_max == 1 and item.card_min == 1:
                self.fields[f"{item.id}"] = self._define_choicefield(item, True, tname, lang)
            elif item.card_max == -1 and item.card_min == 0:
                self.fields[f"{item.id}"] = self._define_multifield(item, False, tname, lang)
            elif item.card_max == -1 and item.card_min == 1:
                self.fields[f"{item.id}"] = self._define_multifield(item, True, tname, lang)

    def cleanx(self, x):
        cleaned_values = []
        for key, value in x.items():
            if isinstance(value, QuerySet):
                for y in value:
                    cleaned_values.append(y.id)
            elif value:
                cleaned_values.append(value)
        return ThesaurusKeyword.objects.filter(id__in=flatten(cleaned_values))

    def _define_multifield(self, item, required, tname, lang):
        return MultipleChoiceField(
            choices=self._get_thesauro_keyword_label(item, lang),
            widget=autocomplete.Select2Multiple(
                url=f"/base/thesaurus_available/?sysid={item.id}&lang={lang}",
                attrs={"class": "treq" if required else ""},
            ),
            label=f"{tname}",
            required=False,
        )

    def _define_choicefield(self, item, required, tname, lang):
        return models.ChoiceField(
            label=f"{tname}",
            required=False,
            widget=forms.Select(attrs={"class": "treq" if required else ""}),
            choices=self._get_thesauro_keyword_label(item, lang))

    @staticmethod
    def _get_thesauro_keyword_label(item, lang):
        qs_local = []
        qs_non_local = [("", "------")]
        for key in ThesaurusKeyword.objects.filter(thesaurus_id=item.id):
            label = ThesaurusKeywordLabel.objects.filter(keyword=key).filter(lang=lang)
            if label.exists():
                qs_local.append((label.get().keyword.id, label.get().label))
            else:
                qs_non_local.append((key.id, key.alt_label))

        return qs_non_local + qs_local

    @staticmethod
    def _get_thesauro_title_label(item, lang):
        tname = ThesaurusLabel.objects.values_list("label", flat=True).filter(thesaurus=item).filter(lang=lang)
        if not tname:
            return Thesaurus.objects.get(id=item.id).title
        return tname.first()


class ResourceBaseDateTimePicker(DateTimePicker):

    def build_attrs(self, base_attrs=None, extra_attrs=None, **kwargs):
        "Helper function for building an attribute dictionary."
        if extra_attrs:
            base_attrs.update(extra_attrs)
        base_attrs.update(kwargs)
        return super(ResourceBaseDateTimePicker, self).build_attrs(base_attrs)
        # return base_attrs


class ResourceBaseForm(TranslationModelForm):
    """Base form for metadata, should be inherited by childres classes of ResourceBase"""
    data_description = forms.CharField(
        label=_("Data description"),
        required=False,
        widget=TinyMCE())
    supplemental_information = forms.CharField(
        label=_("Supplemental information"),
        required=False,
        widget=TinyMCE())
    purpose = forms.CharField(
        label=_("Purpose"),
        required=False,
        widget=TinyMCE())
    constraints_other = forms.CharField(
        label=_("Other constraints"),
        required=False,
        widget=TinyMCE())
    data_quality_statement = forms.CharField(
        label=_("Data quality statement"),
        required=False,
        widget=TinyMCE())
    owner = forms.ModelChoiceField(
        empty_label=_("Owner"),
        label=_("Owner"),
        required=True,
        queryset=get_user_model().objects.exclude(username='AnonymousUser'),
        widget=autocomplete.ModelSelect2(url='autocomplete_profile'))

    date = forms.DateTimeField(
        label=_("Date"),
        localize=True,
        input_formats=['%Y-%m-%d %H:%M %p'],
        widget=ResourceBaseDateTimePicker(options={"format": "YYYY-MM-DD HH:mm a"})
    )
    temporal_extent_start = forms.DateTimeField(
        label=_("Temporal extent start"),
        required=False,
        localize=True,
        input_formats=['%Y-%m-%d %H:%M %p'],
        widget=ResourceBaseDateTimePicker(options={"format": "YYYY-MM-DD HH:mm a"})
    )
    temporal_extent_end = forms.DateTimeField(
        label=_("Temporal extent end"),
        required=False,
        localize=True,
        input_formats=['%Y-%m-%d %H:%M %p'],
        widget=ResourceBaseDateTimePicker(options={"format": "YYYY-MM-DD HH:mm a"})
    )

    poc = forms.ModelChoiceField(
        empty_label=_("Person outside SDI (fill form)"),
        label=_("Point of Contact"),
        required=True,
        queryset=get_user_model().objects.exclude(
            username='AnonymousUser'),
        widget=autocomplete.ModelSelect2(url='autocomplete_profile'))

    metadata_author = forms.ModelChoiceField(
        empty_label=_("Person outside SDI (fill form)"),
        label=_("Metadata author"),
        required=True,
        queryset=get_user_model().objects.exclude(
            username='AnonymousUser'),
        widget=autocomplete.ModelSelect2(url='autocomplete_profile'))

    keywords = TagField(
        label=_("Free-text Keywords"),
        required=False,
        help_text=_("A space or comma-separated list of keywords. Use the widget to select from Hierarchical tree."),
        # widget=TreeWidget(url='autocomplete_hierachical_keyword'), #Needs updating to work with select2
        widget=TaggitSelect2Custom(url='autocomplete_hierachical_keyword'))

    """
    regions = TreeNodeMultipleChoiceField(
        label=_("Regions"),
        required=False,
        queryset=Region.objects.all(),
        level_indicator=u'___')
    """

    def __init__(self, *args, **kwargs):
        super(ResourceBaseForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            help_text = self.fields[field].help_text
            if help_text != '':
                self.fields[field].widget.attrs.update(
                    {
                        'class': 'has-popover',
                        'data-content': help_text,
                        'data-placement': 'right',
                        'data-container': 'body',
                        'data-html': 'true'})

    def disable_keywords_widget_for_non_superuser(self, user):
        if settings.FREETEXT_KEYWORDS_READONLY and not user.is_superuser:
            self['keywords'].field.disabled = True

    def clean_keywords(self):
        keywords = self.cleaned_data['keywords']
        _unsescaped_kwds = []
        for k in keywords:
            _k = ('%s' % re.sub(r'%([A-Z0-9]{2})', r'&#x\g<1>;', k.strip())).split(",")
            if not isinstance(_k, str):
                for _kk in [html.unescape(x.strip()) for x in _k]:
                    # Simulate JS Unescape
                    _kk = _kk.replace('%u', r'\u').encode('unicode-escape').replace(
                        b'\\\\u',
                        b'\\u').decode('unicode-escape') if '%u' in _kk else _kk
                    _hk = HierarchicalKeyword.objects.filter(name__iexact=f'{_kk.strip()}')
                    if _hk and len(_hk) > 0:
                        _unsescaped_kwds.append(str(_hk[0]))
                    else:
                        _unsescaped_kwds.append(str(_kk))
            else:
                _hk = HierarchicalKeyword.objects.filter(name__iexact=_k.strip())
                if _hk and len(_hk) > 0:
                    _unsescaped_kwds.append(str(_hk[0]))
                else:
                    _unsescaped_kwds.append(str(_k))
        return _unsescaped_kwds

    class Meta:
        exclude = (
            'contacts',
            'name',
            'uuid',
            'bbox_polygon',
            'll_bbox_polygon',
            'srid',
            'category',
            'csw_typename',
            'csw_schema',
            'csw_mdsource',
            'csw_type',
            'csw_wkt_geometry',
            'metadata_uploaded',
            'metadata_xml',
            'csw_anytext',
            'popular_count',
            'share_count',
            'thumbnail',
            'charset',
            'rating',
            'detail_url',
            'tkeywords',
            'users_geolimits',
            'groups_geolimits',
            'dirty_state'
        )


class ValuesListField(forms.Field):

    def to_python(self, value):
        if value in validators.EMPTY_VALUES:
            return []

        value = [item.strip() for item in value.split(',') if item.strip()]

        return value

    def clean(self, value):
        value = self.to_python(value)
        self.validate(value)
        self.run_validators(value)
        return value


class BatchEditForm(forms.Form):
    LANGUAGES = (('', '--------'),) + ALL_LANGUAGES
    group = forms.ModelChoiceField(
        label=_('Group'),
        queryset=Group.objects.all(),
        required=False)
    owner = forms.ModelChoiceField(
        label=_('Owner'),
        queryset=get_user_model().objects.all(),
        required=False)
    category = forms.ModelChoiceField(
        label=_('Category'),
        queryset=TopicCategory.objects.all(),
        required=False)
    license = forms.ModelChoiceField(
        label=_('License'),
        queryset=License.objects.all(),
        required=False)
    regions = forms.ModelChoiceField(
        label=_('Regions'),
        queryset=Region.objects.all(),
        required=False)
    date = forms.DateTimeField(
        label=_('Date'),
        required=False)
    language = forms.ChoiceField(
        label=_('Language'),
        required=False,
        choices=LANGUAGES,
    )
    keywords = forms.CharField(required=False)
    ids = forms.CharField(required=False, widget=forms.HiddenInput())


class BatchPermissionsForm(forms.Form):
    group = forms.ModelChoiceField(
        label=_('Group'),
        queryset=Group.objects.all(),
        required=False)
    user = forms.ModelChoiceField(
        label=_('User'),
        queryset=get_user_model().objects.all(),
        required=False)
    permission_type = forms.MultipleChoiceField(
        label=_('Permission Type'),
        required=True,
        widget=forms.CheckboxSelectMultiple,
        choices=(
            ('r', 'Read'),
            ('w', 'Write'),
            ('d', 'Download'),
        ),
    )
    mode = forms.ChoiceField(
        label=_('Mode'),
        required=True,
        widget=forms.RadioSelect,
        choices=(
            ('set', 'Set'),
            ('unset', 'Unset'),
        ),
    )
    ids = forms.CharField(required=False, widget=forms.HiddenInput())


class UserAndGroupPermissionsForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super(UserAndGroupPermissionsForm, self).__init__(*args, **kwargs)
        self.fields['layers'].label_from_instance = self.label_from_instance

    layers = forms.ModelMultipleChoiceField(
        queryset=Layer.objects.all(),
        required=False)
    permission_type = forms.MultipleChoiceField(
        required=True,
        widget=forms.CheckboxSelectMultiple,
        choices=(
            ('r', 'Read'),
            ('w', 'Write'),
            ('d', 'Download'),
        ),
    )
    mode = forms.ChoiceField(
        required=True,
        widget=forms.RadioSelect,
        choices=(
            ('set', 'Set'),
            ('unset', 'Unset'),
        ),
    )
    ids = forms.CharField(required=False, widget=forms.HiddenInput())

    @staticmethod
    def label_from_instance(obj):
        return obj.title


class CuratedThumbnailForm(ModelForm):
    class Meta:
        model = CuratedThumbnail
        fields = ['img']


class OwnerRightsRequestForm(forms.Form):
    resource = forms.ModelChoiceField(
        label=_('Resource'),
        queryset=ResourceBase.objects.all(),
        widget=forms.HiddenInput())
    reason = forms.CharField(
        label=_('Reason'),
        widget=forms.Textarea,
        help_text=_('Short reasoning behind the request'),
        required=True)

    class Meta:
        fields = ['reason', 'resource']


class ThesaurusImportForm(forms.Form):
    rdf_file = forms.FileField()
