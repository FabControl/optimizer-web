from django.shortcuts import render, get_object_or_404, redirect
from django.template import loader
from .models import *

# Create your views here.


def index(request):
    return redirect('dashboard')


def dashboard(request):
    context = {}
    return render(request, 'session/dashboard.html', context)


def material(request, name):
    material = get_object_or_404(Material, name=name)
    context = {'material_name': material.name,
               'size_od': material.size_od,
               'pub_date': material.pub_date}
    return render(request, 'session/material.html', context)


def session_manager(request):
    latest_materials = Material.objects.order_by('-pub_date')[:5]
    materials = Material.objects.all()
    machines = Machine.objects.all()
    context = {'latest_materials': latest_materials,
               'materials': materials,
               'machines': machines}
    return render(request, 'session/session_manager.html', context)


def session(request, session_number):
    session = get_object_or_404(Session, session_number=session_number)
    context = {}
    return render(request, 'session/session.html', context)


def new_session(request):
    context = {}
    return render(request, 'session/new_session.html', context)
