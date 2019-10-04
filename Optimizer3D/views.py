from django.shortcuts import render, get_object_or_404, redirect


def index(request):
    return redirect('session:index')


def error_404_view(request, exception):
    return render(request, "404.html")


def error_500_view(request, exception):
    return render(request, "500.html")
