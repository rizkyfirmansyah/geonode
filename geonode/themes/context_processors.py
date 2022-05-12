
from django.core.cache import cache
from urllib3 import HTTPResponse
from .forms import FeedbackForm
import json
from django.shortcuts import render
from .models import GeoNodeThemeCustomization, THEME_CACHE_KEY


def custom_theme(request):
    theme = cache.get(THEME_CACHE_KEY)
    if theme is None:
        try:
            theme = GeoNodeThemeCustomization.objects.prefetch_related('partners').get(is_enabled=True)
            slides = theme.jumbotron_slide_show.filter(is_enabled=True)
        except Exception:
            theme = {}
            slides = []
        cache.set(THEME_CACHE_KEY, theme)
    else:
        try:
            slides = theme.jumbotron_slide_show.filter(is_enabled=True)
        except Exception:
            slides = []
    return {'custom_theme': theme, 'slides': slides}


def feedback_form(request):
    pass
    # if request.method == 'POST':
    #     form = FeedbackForm(request.POST)
    #     if form.is_valid():
    #         form.save()
    #         out = {'success': True}
    #         return HTTPResponse(
    #             json.dumps(out),
    #             content_type='application/json',
    #             status=200
    #         )
    # else:
    #     form = FeedbackForm()

    # context = {'form': form}
    # return render(request, 'modal/feedbacks.html', context)