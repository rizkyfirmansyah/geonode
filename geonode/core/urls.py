from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^login/$', views.core_login(), name='login'),
]