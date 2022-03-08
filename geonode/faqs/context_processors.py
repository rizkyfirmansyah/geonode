
from django.core.cache import cache

from .models import GeonodeFaq

def custom_faqs(request):
    if faqs is None:
        try:
            faqs = GeonodeFaq.objects.prefetch_related(None).get()
        except Exception:
            faqs = {}
    return {'custom_faqs': faqs}
