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
from allauth.account.forms import ResetPasswordForm, SignupForm, LoginForm, ChangePasswordForm, AddEmailForm
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Column
from hcaptcha.fields import hCaptchaField
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.contrib.auth import password_validation

username_validator = UnicodeUsernameValidator()

# Ported in from django-registration
attrs_dict = {'class': 'required'}


class ProfileCreationForm(UserCreationForm):
    first_name = forms.CharField(max_length=12, min_length=4, required=True, help_text='Required: First Name',
                                widget=forms.TextInput(attrs={'class': 'form-control w-100', 'placeholder': 'First Name'}))
    last_name = forms.CharField(max_length=12, min_length=4, required=True, help_text='Required: Last Name',
                               widget=(forms.TextInput(attrs={'class': 'form-control w-100'})))
    email = forms.EmailField(max_length=50, help_text='Required. Inform a valid email address.',
                             widget=(forms.TextInput(attrs={'class': 'form-control w-100'})))
    password1 = forms.CharField(label=_('Password'),
                                widget=(forms.PasswordInput(attrs={'class': 'form-control w-100'})),
                                help_text=password_validation.password_validators_help_text_html())
    password2 = forms.CharField(label=_('Password Confirmation'), widget=forms.PasswordInput(attrs={'class': 'form-control w-100'}),
                                help_text=_('Just Enter the same password, for confirmation'))
    username = forms.CharField(
        label=_('Username'),
        max_length=150,
        help_text=_('Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.'),
        validators=[username_validator],
        error_messages={'unique': _("A user with that username already exists.")},
        widget=forms.TextInput(attrs={'class': 'form-control w-100'})
    )
    class Meta:
        model = get_user_model()
        fields = ('username', 'first_name', 'last_name', 'email',)

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
  
    hcaptcha = hCaptchaField()

    class Meta:
        fields = '__all__'
        unlabelled_fields = ('remember', 'hcaptcha')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_show_labels = True
        for field in ProfileLoginForm.Meta.unlabelled_fields:
            self.fields[field].label = False

        self.helper.layout = Layout(
            Column('login', css_class='form-group'),
            Column('password', css_class='form-group'),
            Column('remember'),
            Column('hcaptcha'),
            Submit('submit', 'Sign in', css_class='btn btn-primary btn-login w-100')
        )

        self.fields['login'].label = 'E-mail Address or Username'
        # change the style of checkboxinput to toggle instead of boring booleanfield. And remove the label!
        remember_choices=(
            (False, "Go ahead, forget me"),
            (True, "Remember me")
        )
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


class ProfileAddEmailForm(AddEmailForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].widget.attrs['class'] = 'w-100 p-2'
        self.fields['email'].label = ''

    def save(self, request):
        email_address = super().save(request)

        return email_address


class ProfileSignupForm(SignupForm):

    first_name = forms.CharField(max_length=30, label='First Name')
    last_name = forms.CharField(max_length=30, label='Last Name')
    hcaptcha = hCaptchaField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Column('email', css_class='form-group'),
            Column('first_name', css_class='form-group'),
            Column('last_name', css_class='form-group'),
            Column('password1', css_class='form-group'),
            Column('password2', css_class='form-group'),
            Column('hcaptcha', css_class='w-100'),
            Submit('submit', 'Sign up', css_class='btn btn-primary btn-login w-100')
        )

        self.fields['email'].label = 'E-mail Address'
        self.fields['hcaptcha'].label = ''
        self.fields['password1'].widget.attrs['placeholder'] = 'Minimum password length of 6 characters'
        self.fields['password2'].widget.attrs['placeholder'] = 'Confirm again your password'
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
