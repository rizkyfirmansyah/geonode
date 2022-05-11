from geonode.sdi.context_processors import feedback_form
from geonode.sdi.views import faq_view, about_view, help_view
from django.conf.urls import url


urlpatterns = [
    url(r'^faqs/$', faq_view, name='faqs'),
    url(r'^help/$', help_view, name='help'),
    url(r'^about/$', about_view, name='about'),
    # url(r'^feedback/$', feedback_form, name='feedback'),
]