from django.shortcuts import render
from .models import GeonodeFaq

def FAQView(request):
    authenticated_faqs = GeonodeFaq.objects.filter(authenticated_users=True).get()
    anonymous_faqs = GeonodeFaq.objects.filter(authenticated_users=False).get()
    
    return render(request, 'faqs.html', { 'auth_faqs': authenticated_faqs, 'anon_faqs': anonymous_faqs })