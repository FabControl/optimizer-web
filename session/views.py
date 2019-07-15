from django.shortcuts import render
from django.template import loader
from .models import *

# Create your views here.


def index(request):
    latest_materials = Material.objects.order_by('-pub_date')[:5]
    materials = Material.objects.all()
    machines = Machine.objects.all()
    context = {'latest_materials': latest_materials,
               'materials': materials,
               'machines': machines}
    return render(request, 'session/index.html', context)


def material(request, name):
    material = Material.objects.get(name=name)
    context = {'material_name': material.name,
               'size_od': material.size_od,
               'pub_date': material.pub_date}
    return render(request, 'session/material.html', context)


def session(request, session_number):
    try:
        session = Session.objects.get(session_number=session_number)
    context = {}
    return render(request, 'session/new_session.html', context)
