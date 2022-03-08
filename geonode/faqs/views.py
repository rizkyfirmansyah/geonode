from django.shortcuts import render
from .models import GeonodeFaq

def FAQView(request):
    faqs = GeonodeFaq.objects.get()
    return render(request, 'faqs.html', { 'faqs': faqs })