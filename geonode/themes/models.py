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
import logging

from django.db import models
from django.template.defaultfilters import slugify
from django.core.cache import cache
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils.translation import ugettext_noop as _
from imagekit.models import ImageSpecField
from colorfield.fields import ColorField
from uuid_upload_path import upload_to
from django.conf import settings
from django.urls import reverse


THEME_CACHE_KEY = 'enabled_theme'


class Partner(models.Model):
    logo = models.ImageField(upload_to='img/%Y/%m', null=True, blank=True)
    name = models.CharField(max_length=100, help_text="This will not appear anywhere.")
    title = models.CharField(max_length=255, verbose_name="Display name")
    href = models.CharField(max_length=255, verbose_name="Website")

    @property
    def logo_class(self):
        _logo_class = slugify(f"logo_{self.name}")
        return str(_logo_class)

    @property
    def partner_link(self):
        _href = self.href if self.href.startswith('http') else f'http://{self.href}'
        return str(_href)

    def __str__(self):
        return str(self.title)

    class Meta:
        ordering = ("name", )
        verbose_name_plural = 'Partners'


class JumbotronThemeSlide(models.Model):
    slide_name = models.CharField(max_length=255, unique=True)
    jumbotron_slide_image = models.ImageField(
        upload_to='img/%Y/%m', verbose_name="Jumbotron slide background")
    jumbotron_slide_image_thumbnail = ImageSpecField(source='jumbotron_slide_image', options={'quality': 60})
    jumbotron_slide_content = models.TextField(
        null=True, blank=True, verbose_name="Jumbotron slide content",
        help_text=_("Fill in this section with markdown"))
    hide_jumbotron_slide_content = models.BooleanField(
        default=False,
        verbose_name="Hide text in the jumbotron slide",
        help_text=_("Check this if the jumbotron background image already contains text"))
    is_enabled = models.BooleanField(
        default=True,
        help_text=_("Disabling this slide will hide it from the slide show"))

    def __str__(self):
        get_icon = (lambda arg: '[✓]' if arg else '[✗]')
        _enabled_icon = get_icon(self.is_enabled)
        _slide_content_icon = get_icon(self.hide_jumbotron_slide_content)
        return f'{self.slide_name} | <Enabled: {_enabled_icon} -- Hide Text: {_slide_content_icon}>'


class GeoNodeThemeCustomization(models.Model):
    BOOLEAN_CHOICES = [
      ("false", _("False")),
      ("true", _("True"))
    ]

    name = models.CharField(max_length=100, help_text="This will not appear anywhere.")
    date = models.DateTimeField(auto_now_add=True, blank=True, help_text="This will not appear anywhere.")
    description = models.TextField(null=True, blank=True, help_text="This will not appear anywhere.")
    is_enabled = models.BooleanField(
        default=False,
        help_text="Enabling this theme will disable the current enabled theme (if any)")
    favicon = models.ImageField(upload_to='img/%Y/%m', null=True, blank=True, help_text=_("Display favicon ico at browser tab"))
    logo = models.ImageField(upload_to='img/%Y/%m', null=True, blank=True, help_text=_("Display logo at the navigation header"))
    logo_footer = models.ImageField(upload_to='img/%Y/%m', null=True, blank=True, help_text=_("Display logo at the footer"))
    jumbotron_bg = models.ImageField(
        _("Landing page background image"),
        upload_to='img/%Y/%m', null=True, blank=True, help_text=_("Display background image at the landing page"))
    jumbotron_welcome_title = models.CharField(
        _("Landing page title"),
        max_length=255, null=True, blank=True, help_text=_("Landing page welcome title, i.e.: Information Sharing Platform"))
    jumbotron_welcome_content = models.TextField(
        _("Landing page description"),
        null=True, blank=True, help_text=_("Landing page long description, i.e.: Welcome to the Spatial Data Infrastructure"))
    jumbotron_title_color = ColorField(
        _("Landing page title color"),
        default="#ffffff", help_text=_("Landing page welcome title color, default to white"))
    jumbotron_description_color = ColorField(
        _("Landing page description color"),
        default="#ffffff", help_text=_("Landing page long description color, default to white"))
    jumbotron_welcome_hide = models.BooleanField(
        default=False,
        verbose_name="Hide text in the jumbotron",
        help_text="Check this if the jumbotron backgroud image already contains text")
    jumbotron_slide_show = models.ManyToManyField(JumbotronThemeSlide, blank=True)
    modal_login_bg = models.ImageField(
      _("Modal login background image"),
      upload_to='img/%Y/%m', null=True, blank=True, help_text=_("Display image at the login window"))
    welcome_theme = models.CharField(max_length=255, default="JUMBOTRON_BG",
                                     choices=(("JUMBOTRON_BG", "jumbotron background"), ("SLIDE_SHOW", "slide show"),),
                                     help_text=_("Choose between using jumbotron background and slide show"))
    header_bg_color = ColorField(
      _("Header background color"),
      default="#1C463F", help_text=_("Background color of the header pages, default to green"))
    showcase_bg_color = ColorField(
      _("Showcase background color"),
      default="#1C463F", help_text=_("Background color of the showcase landing page, default to green"))
    showcase_text_color = ColorField(default="#ffffff", help_text=_("Text color of the showcase landing page, default to white"))
    showcase_text_link_color = ColorField(default="#fdba12", help_text=_("Text link color of the showcase landing page, default to marigold"))
    body_text_color = ColorField(default="#3a3a3a")
    navbar_color = ColorField(default="#000000", help_text=_("Background color of the navigation bar, default to black"))
    navbar_text_color = ColorField(default="#ffffff")
    navbar_text_hover = ColorField(default="#F39F1E")
    navbar_text_hover_focus = ColorField(default="#F39F1E")
    navbar_dropdown_menu = ColorField(default="#F39F1E")
    navbar_dropdown_menu_text = ColorField(default="#ffffff")
    navbar_dropdown_menu_hover = ColorField(default="#eea200")
    navbar_dropdown_menu_divider = ColorField(default="#eea200")
    search_bg_color = ColorField(
      _("Search background color"),
      default="#000000")
    search_title_color = ColorField(default="#ffffff")
    search_link_color = ColorField(default="#ff8f31")
    textbox_input_color = ColorField(default="#000000", help_text=_("Text color of textbox input, default to white"))
    textbox_bg_color = ColorField(
        _("Textbox background color"),
        default="#F0F2F5", help_text=_("Background color of textbox input, default to green"))
    contactus = models.BooleanField(default=False, verbose_name="Enable contact us box")
    contact_name = models.CharField(max_length=255, null=True, blank=True)
    contact_position = models.CharField(max_length=255, null=True, blank=True)
    contact_administrative_area = models.CharField(max_length=255, null=True, blank=True)
    contact_street = models.CharField(max_length=255, null=True, blank=True)
    contact_postal_code = models.CharField(max_length=255, null=True, blank=True)
    contact_city = models.CharField(max_length=255, null=True, blank=True)
    contact_country = models.CharField(max_length=255, null=True, blank=True)
    contact_delivery_point = models.CharField(max_length=255, null=True, blank=True)
    contact_email = models.CharField(max_length=255, null=True, blank=True)
    partners_title = models.CharField(max_length=100, null=True, blank=True, default="Our Partners")
    partners = models.ManyToManyField(Partner, related_name="partners", blank=True)
    copyright = models.TextField(null=True, blank=True)
    copyright_color = ColorField(default="#F39F1E")
    footer_copyright = models.CharField(max_length=255, null=True, blank=True)
    footer_bg_color = ColorField(
      _("Footer background color"),
      default="#000000", help_text=_("Background color of the footer at the landing page, default to black"))
    footer_text_color = ColorField(default="#ffffff")
    footer_href_color = ColorField(default="#ff8f31")

    # Cookies Law Info Bar
    cookie_law_info_bar_enabled = models.BooleanField(default=True, verbose_name="Cookies Law Info Bar")
    cookie_law_info_bar_head = models.TextField(null=False, blank=False, default="This website uses cookies")
    cookie_law_info_bar_text = models.TextField(
        null=False, blank=False,
        default="""This website uses cookies to improve your experience, \
        check <strong><a style="color:#000000" href="/privacy-policy/">this page</a></strong> for details. \
        We'll assume you're ok with this, but you can opt-out if you wish.""")
    cookie_law_info_leave_url = models.TextField(null=False, blank=False, default="#")
    cookie_law_info_showagain_head = models.TextField(null=False, blank=False, default="Privacy & Cookies Policy")

    cookie_law_info_data_controller = models.TextField(null=False, blank=False, default="#DATA_CONTROLLER")
    cookie_law_info_data_controller_address = models.TextField(
        null=False, blank=False, default="#DATA_CONTROLLER_ADDRESS")
    cookie_law_info_data_controller_phone = models.TextField(null=False, blank=False, default="#DATA_CONTROLLER_PHONE")
    cookie_law_info_data_controller_email = models.TextField(null=False, blank=False, default="#DATA_CONTROLLER_EMAIL")

    # Cookies Law Info Bar settings
    cookie_law_info_animate_speed_hide = models.CharField(max_length=30, default="500")
    cookie_law_info_animate_speed_show = models.CharField(max_length=30, default="500")
    cookie_law_info_background = ColorField(default="#F39F1E")
    cookie_law_info_border = ColorField(default="#444")
    cookie_law_info_border_on = models.CharField(max_length=30, default="false", choices=BOOLEAN_CHOICES)
    cookie_law_info_button_1_button_colour = ColorField(default="#000")
    cookie_law_info_button_1_button_hover = ColorField(default="#000000")
    cookie_law_info_button_1_link_colour = ColorField(default="#F39F1E")
    cookie_law_info_button_1_as_button = models.CharField(max_length=30, default="true", choices=BOOLEAN_CHOICES)
    cookie_law_info_button_1_new_win = models.CharField(max_length=30, default="true", choices=BOOLEAN_CHOICES)
    cookie_law_info_button_2_button_colour = ColorField(default="#000000")
    cookie_law_info_button_2_button_hover = ColorField(default="#000000")
    cookie_law_info_button_2_link_colour = ColorField(default="#F39F1E")
    cookie_law_info_button_2_as_button = models.CharField(max_length=30, default="true", choices=BOOLEAN_CHOICES)
    cookie_law_info_button_2_hidebar = models.CharField(max_length=30, default="true", choices=BOOLEAN_CHOICES)
    cookie_law_info_button_3_button_colour = ColorField(default="#000")
    cookie_law_info_button_3_button_hover = ColorField(default="#000000")
    cookie_law_info_button_3_link_colour = ColorField(default="#F39F1E")
    cookie_law_info_button_3_as_button = models.CharField(max_length=30, default="true", choices=BOOLEAN_CHOICES)
    cookie_law_info_button_3_new_win = models.CharField(max_length=30, default="false", choices=BOOLEAN_CHOICES)
    cookie_law_info_button_4_button_colour = ColorField(default="#000")
    cookie_law_info_button_4_button_hover = ColorField(default="#000000")
    cookie_law_info_button_4_link_colour = ColorField(default="#F39F1E")
    cookie_law_info_button_4_as_button = models.CharField(max_length=30, default="true", choices=BOOLEAN_CHOICES)
    cookie_law_info_font_family = models.CharField(max_length=30, default="inherit")
    cookie_law_info_header_fix = models.CharField(max_length=30, default="false", choices=BOOLEAN_CHOICES)
    cookie_law_info_notify_animate_hide = models.CharField(max_length=30, default="true", choices=BOOLEAN_CHOICES)
    cookie_law_info_notify_animate_show = models.CharField(max_length=30, default="false", choices=BOOLEAN_CHOICES)
    cookie_law_info_notify_div_id = models.CharField(max_length=30, default="#cookie-law-info-bar")
    cookie_law_info_notify_position_horizontal = models.CharField(max_length=30, default="right")
    cookie_law_info_notify_position_vertical = models.CharField(max_length=30, default="bottom")
    cookie_law_info_scroll_close = models.CharField(max_length=30, default="false", choices=BOOLEAN_CHOICES)
    cookie_law_info_scroll_close_reload = models.CharField(max_length=30, default="false", choices=BOOLEAN_CHOICES)
    cookie_law_info_accept_close_reload = models.CharField(max_length=30, default="false", choices=BOOLEAN_CHOICES)
    cookie_law_info_reject_close_reload = models.CharField(max_length=30, default="false", choices=BOOLEAN_CHOICES)
    cookie_law_info_showagain_tab = models.CharField(max_length=30, default="true", choices=BOOLEAN_CHOICES)
    cookie_law_info_showagain_background = models.CharField(max_length=30, default="#fff")
    cookie_law_info_showagain_border = ColorField(default="#000")
    cookie_law_info_showagain_div_id = models.CharField(max_length=30, default="#cookie-law-info-again")
    cookie_law_info_showagain_x_position = models.CharField(max_length=30, default="30px")
    cookie_law_info_text = ColorField(default="#000000")
    cookie_law_info_link_text = ColorField(default="#ffffff")
    cookie_law_info_show_once_yn = models.CharField(max_length=30, default="false", choices=BOOLEAN_CHOICES)
    cookie_law_info_show_once = models.CharField(max_length=30, default="10000")
    cookie_law_info_logging_on = models.CharField(max_length=30, default="false", choices=BOOLEAN_CHOICES)
    cookie_law_info_as_popup = models.CharField(max_length=30, default="false", choices=BOOLEAN_CHOICES)
    cookie_law_info_popup_overlay = models.CharField(max_length=30, default="true", choices=BOOLEAN_CHOICES)
    cookie_law_info_bar_heading_text = models.CharField(max_length=30, default="This website uses cookies")
    cookie_law_info_cookie_bar_as = models.CharField(max_length=30, default="banner")
    cookie_law_info_popup_showagain_position = models.CharField(max_length=30, default="bottom-right")
    cookie_law_info_widget_position = models.CharField(max_length=30, default="left")

    def file_link(self):
        if self.logo:
            return f"<a href='{self.logo.url}'>download</a>"
        else:
            return "No attachment"

    file_link.allow_tags = True

    @property
    def theme_uuid(self):
        if not self.identifier:
            self.identifier = slugify(f"theme id {self.id} {self.date}")
        return str(self.identifier)

    def __str__(self):
        return str(self.name)

    class Meta:
        ordering = ("date", )
        verbose_name_plural = 'Themes'



logger = logging.getLogger(__name__)

class Faq(models.Model):

    AUTHENTICATED_CHOICES = [
      (False, _("For anyone including not a registered user")),
      (True, _("Certainly yes!"))
    ]

    header_title = models.CharField(max_length=255, verbose_name=_("Title Page"), default="Frequently Asked Questions", null=True, blank=True)
    header_title_color = ColorField(default="#000000", verbose_name=_("Set the text color of the title"), null=True, blank=True)
    contents = models.TextField(verbose_name=_("Content of the FAQs page"), null=True, blank=True)
    authenticated_users = models.BooleanField(default=True, verbose_name=_("Display for registered users?"), choices=AUTHENTICATED_CHOICES)
    created_at = models.DateTimeField(_('Created Date'), auto_now_add=True, blank=True, null=True)
    last_update = models.DateTimeField(_('Created Date'), auto_now=True, blank=True, null=True)

    def __str__(self):
        return str(self.header_title)

    def get_absolute_url(self):
        return reverse("faq", kwargs={"pk": self.pk})

    class Meta:
        ordering = ("id", )
        verbose_name_plural = 'SDI FAQs'


class About(models.Model):

    header_title = models.CharField(max_length=255, verbose_name=_("Title Page"), default=_("About SDI"), null=True, blank=True)
    header_title_color = ColorField(default="#000000", verbose_name=_("Set the text color of the title"), null=True, blank=True)
    contents = models.TextField(verbose_name=_("Content of the About page"), null=True, blank=True)
    created_at = models.DateTimeField(_('Created Date'), auto_now_add=True, blank=True, null=True)
    last_update = models.DateTimeField(_('Created Date'), auto_now=True, blank=True, null=True)

    class Meta:
        ordering = ("id", )
        verbose_name_plural = 'SDI About'

    def __str__(self):
        return str(self.header_title)

    def get_absolute_url(self):
        return reverse("about", kwargs={"pk": self.pk})


class Help(models.Model):

    header_title = models.CharField(max_length=255, verbose_name=_("Title Page"), default=_("Help & Support"), null=True, blank=True)
    header_title_color = ColorField(default="#000000", verbose_name=_("Set the text color of the title"), null=True, blank=True)
    contents = models.TextField(verbose_name=_("Content of the Help & Support page"), null=True, blank=True)
    created_at = models.DateTimeField(_('Created Date'), auto_now_add=True, blank=True, null=True)
    last_update = models.DateTimeField(_('Created Date'), auto_now=True, blank=True, null=True)

    class Meta:
        ordering = ("id", )
        verbose_name_plural = 'SDI Help & Support'

    def __str__(self):
        return str(self.header_title)

    def get_absolute_url(self):
        return reverse("help", kwargs={"pk": self.pk})


class Feedback(models.Model):
    feedback_file_help_text = _("add a Screenshot or Video (recommended)")
    details_help_text = _("please include as much information as possible..")
    feedback_url_help_text = _("provide the url when the trouble happens")
    user_help_text = _("reported by")

    uuid = models.CharField(max_length=36)
    title = models.TextField(
        _("Choose an area"),
        null=True,
        blank=True)
    details = models.TextField(
        _("Details"),
        null=True,
        blank=True,
        help_text=details_help_text)
    feedback_url = models.URLField(
      _("URL"),
      blank=True,
      null=True,
      max_length=255,
      help_text=feedback_url_help_text)
    feedback_file = models.FileField(
        upload_to=upload_to,
        null=True,
        blank=True,
        max_length=255,
        verbose_name=feedback_file_help_text)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, help_text=user_help_text, null=True)
    created_at = models.DateTimeField(_('Created Date'), auto_now_add=True, blank=True, null=True)

    class Meta:
        ordering = ("id", )
        verbose_name_plural = 'SDI Feedbacks'
    
    def __str__(self):
        return str(self.title)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)


@receiver(post_save, sender=Feedback)
def post_save_feedback(sender, instance, created, *args, **kwargs):
    from .tasks import create_feedback

    if created:
        if instance.id and instance.feedback_file:
            create_feedback.apply_async((instance.id,))

        instance.save()


# Disable other themes if one theme is enabled.
@receiver(post_save, sender=GeoNodeThemeCustomization)
def disable_other(sender, instance, **kwargs):
    if instance.is_enabled:
        GeoNodeThemeCustomization.objects.exclude(pk=instance.pk).update(is_enabled=False)


# Invalidate the cached theme if a partner or a theme is updated.
@receiver(post_save, sender=GeoNodeThemeCustomization)
@receiver(post_save, sender=Partner)
@receiver(post_delete, sender=GeoNodeThemeCustomization)
@receiver(post_delete, sender=Partner)
def invalidate_cache(sender, instance, **kwargs):
    cache.delete(THEME_CACHE_KEY)
