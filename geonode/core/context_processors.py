from .forms import CoreLoginForm, CoreSignupForm


def CoreForm(request):
    return {
        'login_form': CoreLoginForm(),
        'signup_form': CoreSignupForm()
    }