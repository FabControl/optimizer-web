from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth import authenticate, login, logout


# Create your views here.
def user_login(request):
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


def user_logout(request):
    logout(request)
    return redirect("login")
