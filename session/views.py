from django.shortcuts import render, get_object_or_404, redirect
from .utilities import load_json
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


class SessionView(generic.DetailView):
    model = Session
    template_name = 'session/session.html'


def new_session(request):
    target_descriptions = load_json("session/static/session/json/target_descriptions.json")
    materials = Material.objects.order_by('pub_date')
    machines = Machine.objects.order_by('pub_date')
    context = {"materials": materials,
               "machines": machines,
               "target_descriptions": target_descriptions}
    return render(request, 'session/new_session.html', context)


def faq(request):
    context = {}
    return render(request, 'session/faq.html', context)


def quick_start(request):
    context = {}
    return render(request, 'session/quick_start.html', context)


def support(request):
    context = {}
    return render(request, 'session/support.html', context)


def guide(request):
    context = {}
    return render(request, 'session/guide.html', context)
