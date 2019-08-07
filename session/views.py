from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .utilities import load_json
from django.template import loader
from .models import *
from django.views import generic
from .forms import NewTestForm, SessionForm, MaterialForm, MachineForm

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


class MaterialsView(generic.ListView):
    template_name = "session/material_manager.html"
    context_object_name = 'materials'

    def get_queryset(self):
        return Material.objects.order_by('pub_date')


class MaterialView(generic.DetailView):
    model = Material
    template_name = 'session/material_detail.html'


def material_form(request):
    if request.method == 'POST':
        form = MaterialForm(request.POST)
        if form.is_valid():
            messages.info(request, 'The material has been created!')
            form.save()
    else:
        form = MaterialForm()
    context = {"form": form}
    return render(request, 'session/material_form.html', context)


class MachineView(generic.DetailView):
    model = Machine
    template_name = 'session/machine_detail.html'
    

class MachinesView(generic.ListView):
    template_name = "session/machine_manager.html"
    context_object_name = 'machines'

    def get_queryset(self):
        return Machine.objects.order_by('pub_date')


def machine_form(request):
    if request.method == 'POST':
        form = MachineForm(request.POST)
        if form.is_valid():
            messages.info(request, 'The machine has been created!')
            form.save()
    else:
        form = MachineForm()
    context = {"form": form}
    return render(request, 'session/machine_form.html', context)


class SettingView(generic.DetailView):
    model = Settings
    template_name = 'session/settings_detail.html'


class SettingsView(generic.ListView):
    template_name = "session/settings_manager.html"
    context_object_name = 'settings'

    def get_queryset(self):
        return Settings.objects.order_by('pub_date')


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


# class FormsTestView(generic.TemplateView):
#     template_name = "session/form_test.html"
#     form = NewTestForm(request.POST)
#
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         context['latest_articles'] = Article.objects.all()[:5]
#         return context


def form_test(request):
    if request.method == 'POST':
        form = SessionForm(request.POST)
    else:
        form = SessionForm()

    context = {"form": form}

    return render(request, 'session/form_test.html', context)


def testing_session(request):
    target_descriptions = load_json("session/static/session/json/target_descriptions.json")
    print(target_descriptions)
    context = {"target_descriptions": target_descriptions}
    return render(request, 'session/testing_session.html', context)
