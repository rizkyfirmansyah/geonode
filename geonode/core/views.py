from geonode.core.forms import CoreLoginForm
from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils.translation import ugettext as _


def core_login(request):

    if 'next' in request.GET:
        title = _("Login Required")
        message = _("Please login before proceed to explore.")
        messages.add_message(request, messages.INFO, message, extra_tags=title)
    if request.method == 'POST':
        form = CoreLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]
            remember_me = form.cleaned_data['remember_me']
            user = authenticate(username=username, password=password)
            if user:
                login(request, user)
                if not remember_me:
                    request.session.set_expiry(0)
                    return redirect('accounts:home')
                else:
                    request.session.set_expiry(1209600)
                    return redirect('accounts:home')
            else:
                return redirect('accounts:login')
        else:
            return redirect('accounts:register')
    else:
        form = CoreLoginForm()
        return render(request, "login.html", {'form': form})