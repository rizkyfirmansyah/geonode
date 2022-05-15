from .forms import RodaForm
from django.contrib.auth.decorators import login_required
from geonode.notifications_helper import toast_message
from django.shortcuts import render
import uuid


@login_required
def roda_form(request):
    if request.method == 'POST':
        toast_title = _("Submit Feedback")
        roda_form = RodaForm(request.POST)
        if roda_form.is_valid():
            feedback = roda_form.save(commit=False)
            feedback.user_id = request.user.id
            feedback.uuid = str(uuid.uuid4())
            feedback.save()
            message = _("Thank you for your feedback :)")

            return toast_message(request, message, extra_tags=toast_title, redirect=True)

    else:
        roda_form = RodaForm()
        context = {'roda_form': roda_form}
        return render(request, 'modal/request_data.html', context)