from .views import FeedbackDetailView, faq_view, about_view, help_view, feedback_form
from django.conf.urls import url


urlpatterns = [
    url(r'^faqs/$', faq_view, name='faqs'),
    url(r'^help/$', help_view, name='help'),
    url(r'^about/$', about_view, name='about'),
    url(r'^feedback/from/user/$', feedback_form, name='feedback'),
    url(r'^feedbacks/$', FeedbackDetailView.as_view(), name='feedback_list'),
]