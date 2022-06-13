
from django.core.cache import cache

from geonode.datasets.forms import RodaForm
from geonode.people.forms import ProfileSignupForm, ProfileLoginForm, ProfileChangePasswordForm, ProfileAddEmailForm
from geonode.groups.forms import PermissionsForm
from .forms import FeedbackForm
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


def ModalForm(request):
    return {
        'feedback_form': FeedbackForm(),
        'roda_form': RodaForm(),
        'signup_form': ProfileSignupForm(),
        'login_form': ProfileLoginForm(),
        'change_pwd_form': ProfileChangePasswordForm(),
        'add_email_form': ProfileAddEmailForm(),
        'permissions_form': PermissionsForm()
    }