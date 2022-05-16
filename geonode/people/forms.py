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

import taggit

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.utils.translation import ugettext as _
from geonode.base.models import ContactRole
from allauth.account.forms import ResetPasswordForm, SignupForm, LoginForm, ChangePasswordForm


# Ported in from django-registration
attrs_dict = {'class': 'required'}


class ProfileCreationForm(UserCreationForm):

    class Meta:
        model = get_user_model()
        fields = ("username",)

    def clean_username(self):
        # Since User.username is unique, this check is redundant,
        # but it sets a nicer error message than the ORM. See #13147.
        username = self.cleaned_data["username"]
        try:
            get_user_model().objects.get(username=username)
        except get_user_model().DoesNotExist:
            return username
        raise forms.ValidationError(
            self.error_messages['duplicate_username'],
            code='duplicate_username',
        )


class ProfileLoginForm(LoginForm):
  
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['login'].widget.attrs['class'] = 'form-control'
        self.fields['password'].widget.attrs['class'] = 'form-control'
        self.fields['login'].label = 'Email Address or Username'
        # change the style of checkboxinput to toggle instead of boring booleanfield. And remove the label!
        remember_choices=(
            (False, "Go ahead, forget me"),
            (True, "Remember me")
        )
        self.fields['remember'].label = ''
        self.fields['remember'].widget.attrs.update({
                    'data-toggle': 'toggle',
                    'data-width': '100%',
                    'data-height': 'auto',
                    'data-on': remember_choices[0][1],
                    'data-off': remember_choices[1][1],
                    'value': remember_choices[0][0],
                    'data-onstyle': 'info',
                    'data-offstyle': 'primary'})

    def login(self, *args, **kwargs):
        return super().login(*args, **kwargs)


class ProfileResetPasswordForm(ResetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].widget.attrs['class'] = 'w-100 p-2'
        self.fields['email'].label = ''

    def save(self, request):
        email_address = super().save(request)

        return email_address


class ProfileChangePasswordForm(ChangePasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].help_text = 'Set your new password more than 6 characters.'
        self.fields['password2'].help_text = 'Confirm again your new password here.'


class ProfileSignupForm(SignupForm):

    first_name = forms.CharField(max_length=30, label='First Name')
    last_name = forms.CharField(max_length=30, label='Last Name')
  
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['first_name'].widget.attrs['class'] = 'form-control'
        self.fields['last_name'].widget.attrs['class'] = 'form-control'
        self.fields['email'].label = 'Email Address'
        self.fields.pop('username',)

    def signup(self, request, user):
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.save()

        return user

    class Meta:
        model = get_user_model()
        fields = ("first_name", "last_name", "email",)


class ProfileChangeForm(UserChangeForm):

    class Meta:
        model = get_user_model()
        fields = '__all__'


class ForgotUsernameForm(forms.Form):
    email = forms.EmailField(widget=forms.TextInput(attrs=dict(attrs_dict,
                                                               maxlength=75)),
                             label=_('Email Address'))


class RoleForm(forms.ModelForm):

    class Meta:
        model = ContactRole
        exclude = ('contact', 'layer')


class PocForm(forms.Form):
    contact = forms.ModelChoiceField(label="New point of contact",
                                     queryset=get_user_model().objects.all())


class ProfileForm(forms.ModelForm):
    keywords = taggit.forms.TagField(
        label=_("Keywords"),
        required=False,
        help_text=_("A space or comma-separated list of keywords"))

    class Meta:
        model = get_user_model()
        exclude = (
            'user',
            'password',
            'last_login',
            'groups',
            'user_permissions',
            'username',
            'is_staff',
            'is_superuser',
            'is_active',
            'date_joined'
        )
