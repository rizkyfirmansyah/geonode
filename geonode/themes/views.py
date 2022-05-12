import json
from django.shortcuts import render
from urllib3 import HTTPResponse

from .forms import FeedbackForm
from .models import Faq, Help, About


def faq_view(request):
    if Faq.objects.filter(authenticated_users=True).exists():
        authenticated_faqs = Faq.objects.filter(authenticated_users=True).get()
    else:
        authenticated_faqs = None

    if Faq.objects.filter(authenticated_users=False).exists():
        anonymous_faqs = Faq.objects.filter(authenticated_users=False).get()
    else:
        anonymous_faqs = None

    return render(request, 'faqs.html', {'auth_faqs': authenticated_faqs, 'anon_faqs': anonymous_faqs})


def about_view(request):
    if About.objects.all().exists():
        contents = About.objects.get(pk=1)
    else:
        contents = None
    
    return render(request, 'about.html', {'contents': contents})


def help_view(request):
    if Help.objects.all().exists():
        contents = Help.objects.get(pk=1)
    else:
        contents = None
    
    return render(request, 'help.html', {'contents': contents})


def feedback_form(request):
    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            form.save()
            out = {'success': True}
            return HTTPResponse(
                json.dumps(out),
                content_type='application/json',
                status=200
            )
    else:
        form = FeedbackForm()

    context = {'form': form}
    return render(request, 'modal/feedbacks.html', context)