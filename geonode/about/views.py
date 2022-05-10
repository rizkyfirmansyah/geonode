from django.shortcuts import render
from .models import Help, About


def AboutView(request):
    if About.objects.all().exists():
        contents = About.objects.get(pk=1)
    else:
        contents = None
    
    return render(request, 'about.html', {'contents': contents})


def HelpView(request):
    if Help.objects.all().exists():
        contents = Help.objects.get(pk=1)
    else:
        contents = None
    
    return render(request, 'help.html', {'contents': contents})
