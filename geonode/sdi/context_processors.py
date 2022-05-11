from urllib3 import HTTPResponse
from .forms import FeedbackForm
import json
from django.shortcuts import render


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