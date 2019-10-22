from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth import authenticate, login, logout
from .forms import SignUpForm, ResetPasswordForm
from django.views import generic


# Create your views here.
def user_login(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
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
                return HttpResponse("Your account was inactive.")
        else:
            print("Someone tried to login and failed.")
            print("They used username: {} and password: {}".format(email, password))
            return redirect("login")
    else:
        return render(request, 'authentication/login.html', {})


def user_signup(request):
    context = {"form": SignUpForm}
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save_and_notify()
            login(request, user)
            if "next" in request.GET:
                return redirect(request.GET["next"])
            else:
                return redirect('dashboard')
        else:
            return render(request, 'authentication/signup.html', context)
    else:
        return render(request, 'authentication/signup.html', context)


def user_logout(request):
    logout(request)
    return redirect("login")


def password_reset(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = ResetPasswordForm(request.POST)
        if form.is_valid():
            form.save(request)
            return redirect('password_reset_done')

    return render(request, 'authentication/password_reset.html', {'form': ResetPasswordForm})

