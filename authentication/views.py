import simplejson as json
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.utils.datastructures import MultiValueDictKeyError
from .forms import SignUpForm, ResetPasswordForm
from django.views import generic

from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from .forms import SignUpForm


# Create your views here.
def user_login(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = request.POST.get('email')
            password = request.POST.get('password')
            user = authenticate(email=email, password=password)
            if user:
                if user.is_active:
                    login(request, user)
                    if "next" in request.GET:
                        return redirect(request.GET["next"])
                    else:
                        return redirect('dashboard')
                else:
                    messages.error(request, "Your account has been deactivated.")
                    return render(request, 'authentication/login.html', {'form': LoginForm()})
            else:
                messages.error(request, "Failed to log in!")
                return redirect("login")
        else:
            print(form.errors)
            messages.error(request, "Failed to log in!")
            return render(request, 'authentication/login.html', {'form': LoginForm(), 'form_errors': form.errors})
    else:
        return render(request, 'authentication/login.html', {'form': LoginForm()})


def user_signup(request):
    context = {"form": SignUpForm}
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save_and_notify(request)
            login(request, user)
            if "next" in request.GET:
                return redirect(request.GET["next"])
            else:
                return redirect('dashboard')
        else:
            return render(request, 'authentication/signup.html', context)
    else:
        return render(request, 'authentication/signup.html', context)


@login_required
def onboarding_toggler(request):
    if request.method == "POST":
        try:
            sections = request.POST["section"]
        except MultiValueDictKeyError:
            sections = request.POST["section[]"]
        if type(sections) != list:
            sections = [sections]
        mode = request.POST["mode"]
        user = request.user
        temp_sections = user.onboarding_sections

        result = {'success': True, 'section_added': [], 'section_removed': []}

        if mode == 'true':
            for section in sections:
                if section not in user.onboarding_sections:
                    temp_sections.append(section)
                    result["section_added"].append(section)
        else:
            for section in sections:
                if section in user.onboarding_sections:
                    temp_sections.remove(section)
                    result["section_removed"].append(section)

        user.onboarding_sections = temp_sections
        user.save()
        return HttpResponse(result, content_type='application/json')


@login_required
def onboarding_disable(request):
    path = reverse_lazy("dashboard")
    if "next" in request.GET:
        path = request.GET["next"]
    user = request.user
    user.onboarding = False
    user.save()
    result = {"success": True}
    return HttpResponse(json.dumps(result), content_type='application/json')


@login_required
def onboarding_reset(request):
    user = request.user
    user.onboarding_reset()


@login_required
def user_logout(request):
    logout(request)
    return redirect("login")


def password_reset(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = ResetPasswordForm(request.POST)
        if form.is_valid():
            form.save(request=request)
            return redirect('password_reset_done')

    return render(request, 'authentication/password_reset.html', {'form': ResetPasswordForm})

