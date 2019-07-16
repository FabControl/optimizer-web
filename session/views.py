from django.shortcuts import render, get_object_or_404, redirect
from django.template import loader
from .models import *
from django.views import generic

# Create your views here.


def index(request):
    return redirect('dashboard')


def dashboard(request):
    latest_sessions = Session.objects.order_by('number')[:5]
    context = {'latest_sessions': latest_sessions}
    return render(request, 'session/dashboard.html', context)


def material(request, name):
    material = get_object_or_404(Material, name=name)
    context = {'material_name': material.name,
               'size_od': material.size_od,
               'pub_date': material.pub_date}
    return render(request, 'session/material.html', context)


class MaterialView(generic.DetailView):
    model = Material
    template_name = 'session/material_detail.html'


class MachineView(generic.DetailView):
    model = Machine
    template_name = 'session/machine_detail.html'


class SessionListView(generic.ListView):
    template_name = "session/session_manager.html"
    context_object_name = 'sessions'

    def get_queryset(self):
        return Session.objects.order_by('pub_date')


# def session_manager(request):
#     latest_materials = Material.objects.order_by('-pub_date')[:5]
#     materials = Material.objects.all()
#     machines = Machine.objects.all()
#     context = {'latest_materials': latest_materials,
#                'materials': materials,
#                'machines': machines}
#     return render(request, 'session/session_manager.html', context)


class SessionView(generic.DetailView):
    model = Session
    template_name = 'session/session.html'


def new_session(request):
    context = {}
    return render(request, 'session/new_session.html', context)
