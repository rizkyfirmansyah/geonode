from django.shortcuts import render
from .models import Site
from django.shortcuts import get_object_or_404
from django.http import Http404


def FAQView(request):
    if Site.objects.filter(authenticated_users=True).exists():
      authenticated_faqs = Site.objects.filter(authenticated_users=True).get()
    else:
      authenticated_faqs = None
    
    if Site.objects.filter(authenticated_users=False).exists():
      anonymous_faqs = Site.objects.filter(authenticated_users=False).get()
    else:
      anonymous_faqs = None
      
    return render(request, 'faqs.html', { 'auth_faqs': authenticated_faqs, 'anon_faqs': anonymous_faqs })