from django.shortcuts import render
from django.utils.translation import ugettext as _
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView
import uuid
from geonode.messaging.notifications import send_inbox
from geonode.notifications_helper import toast_message
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.contrib.auth import get_user_model
from django.db.models import Q

from .forms import FeedbackForm
from .models import Faq, Feedback, Help, About


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


@login_required
def feedback_form(request):
    if request.method == 'POST':
        toast_title = _("Submit Feedback")
        feedback_form = FeedbackForm(request.POST, request.FILES)
        if feedback_form.is_valid():
            feedback = feedback_form.save(commit=False)
            feedback.user_id = request.user.id
            feedback.uuid = str(uuid.uuid4())
            feedback.save()
            message = _("Thank you for your feedback :)")

            subject = _("User Feedbacks")
            content = f"New Feedback is coming from user: {request.user}"
            send_inbox(request, subject, content, send_to = get_user_model().objects.filter(is_superuser=True)[0])

            return toast_message(request, message, extra_tags=toast_title)

    else:
        feedback_form = FeedbackForm()
        context = {'feedback_form': feedback_form}
        return render(request, 'modal/feedbacks.html', context)


@method_decorator(staff_member_required, name='dispatch')
class FeedbackDetailView(LoginRequiredMixin, ListView):
    model = Feedback
    template_name = "feedbacks.html"
    fields = ['title', 'details', 'feedback_file', 'user', 'created_at']
    context_object_name = 'feedback_list'

    def get_queryset(self):
        return Feedback.objects.all()
