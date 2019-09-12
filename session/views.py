from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.staticfiles import finders
from django.urls import reverse_lazy
from .utilities import load_json, optimizer_info
from django.http import FileResponse, Http404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin

from .models import *
from django.views import generic
from .forms import *

from config import config
from optimizer_api import api_client

# Create your views here.


def index(request):
    # return redirect('dashboard')
    raise Http404("Page not found")


@login_required
def dashboard(request):
    latest_sessions = Session.objects.filter(owner=request.user).order_by('pk')[:5]
    context = {'latest_sessions': latest_sessions}
    return render(request, 'session/dashboard.html', context)


@login_required
def material(request, name):
    material = get_object_or_404(Material, name=name)
    context = {'material_name': material.name,
               'size_od': material.size_od,
               'pub_date': material.pub_date}
    return render(request, 'session/material.html', context)


class MaterialsView(LoginRequiredMixin, generic.ListView):
    template_name = "session/material_manager.html"
    context_object_name = 'materials'

    def get_queryset(self):
        return Material.objects.order_by('pub_date')


class MaterialView(LoginRequiredMixin, generic.DetailView):
    model = Material
    template_name = 'session/material_detail.html'


@login_required
def material_form(request):
    if request.method == 'POST':
        form = MaterialForm(request.POST)
        if form.is_valid():
            messages.info(request, 'The material has been created!')
            form.save()
            return redirect("material_manager")
    else:
        form = MaterialForm()
    context = {"form": form}
    return render(request, 'session/material_form.html', context)


class MachineView(LoginRequiredMixin, generic.DetailView):
    model = Machine
    template_name = 'session/machine_detail.html'


class MachinesView(LoginRequiredMixin, generic.ListView):
    template_name = "session/machine_manager.html"
    context_object_name = 'machines'

    def get_queryset(self):
        return Machine.objects.order_by('pub_date')


@login_required
def machine_form(request):
    if request.method == 'POST':
        self_form = NewMachineForm(request.POST)
        extruder_form = NewExtruderForm(request.POST)
        nozzle_form = NewNozzleForm(request.POST)
        chamber_form = NewChamberForm(request.POST)
        printbed_form = NewPrintbedForm(request.POST)
        extruder = None
        if self_form.is_valid():
            machine = self_form.save(commit=False)
            if extruder_form.is_valid():
                extruder = extruder_form.save(commit=False)
                extruder.nozzle = nozzle_form.save()
                extruder.save()
            if chamber_form.is_valid():
                machine.chamber = chamber_form.save()
            if printbed_form.is_valid():
                machine.printbed = printbed_form.save()
            messages.info(request, 'The machine has been created!')
            machine.extruder = extruder
            machine.save()
            return redirect('machine_manager')
    else:
        self_form = NewMachineForm()
        extruder_form = NewExtruderForm()
        nozzle_form = NewNozzleForm()
        chamber_form = NewChamberForm()
        printbed_form = NewPrintbedForm()
    context = {"self_form": self_form,
               "extruder_form": extruder_form,
               "nozzle_form": nozzle_form,
               "chamber_form": chamber_form,
               "printbed_form": printbed_form}
    return render(request, 'session/machine_form.html', context)


class SettingView(LoginRequiredMixin, generic.DetailView):
    model = Settings
    template_name = 'session/settings_detail.html'


class SettingsView(LoginRequiredMixin, generic.ListView):
    template_name = "session/settings_manager.html"
    context_object_name = 'settings'

    def get_queryset(self):
        return Settings.objects.order_by('pub_date')


class SessionListView(LoginRequiredMixin, generic.ListView):
    template_name = "session/session_manager.html"
    context_object_name = 'sessions'

    def get_queryset(self):
        # queryset = super(SessionListView, self).get_queryset()
        queryset = Session.objects.filter(owner=self.request.user).order_by('pub_date')
        return queryset


class SessionView(LoginRequiredMixin, generic.UpdateView):
    model = Session
    form_class = TestGenerateForm
    template_name = 'session/session.html'

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)
        context['routine'] = api_client.get_routine()
        return context

    def form_valid(self, form):
        session = form.save(commit=False)
        logging.getLogger("views").info("Form valid!")
        # Do any custom stuff here
        session.persistence = api_client.return_data(session.persistence, "persistence")
        session.save()
        return redirect('session_detail', pk=session.pk)


class SessionValidateView(SessionView):
    form_class = TestValidateForm

    def form_valid(self, form):
        session = form.save(commit=False)
        session.alter_previous_tests(-1, "validated", True)
        session = form.save(commit=True)
        if self.request.method == "POST" and "btnprimary" in self.request.POST:
            return redirect('session_next_test', pk=session.pk, priority="primary")
        else:
            return redirect('session_next_test', pk=session.pk, priority="any")

    def form_invalid(self, form):
        import pdb;
        pdb.set_trace()
        session = form.save(commit=False)
        return redirect('session_validate_back', pk=session.pk)


@login_required
def generate_or_validate(request, pk):
    session = Session.objects.get(pk=pk)
    if session.executed:
        logging.getLogger("views").info("Initializing Session validate view!")
        return SessionValidateView.as_view()(request, pk=pk)
    else:
        logging.getLogger("views").info("Initializing Sessionview!")
        return SessionView.as_view()(request, pk=pk)


class SessionDelete(LoginRequiredMixin, generic.DeleteView):
    model = Session
    success_url = reverse_lazy('session_manager')


class MachineDelete(LoginRequiredMixin, generic.DeleteView):
    model = Machine
    success_url = reverse_lazy('machine_manager')


class MaterialDelete(LoginRequiredMixin, generic.DeleteView):
    model = Material
    success_url = reverse_lazy('material_manager')


@login_required
def session_validate_undo(request, pk):
    session = Session.objects.get(pk=pk)
    session.remove_last_test()

    previously_tested_parameters = session.previously_tested_parameters
    del previously_tested_parameters[session.test_number]
    session._previously_tested_parameters = json.dumps(previously_tested_parameters)
    session.save()

    return redirect('session_detail', pk=pk)


@login_required
def session_validate_revert(request, pk):
    session = Session.objects.get(pk=pk)

    routine = api_client.get_routine()
    test_names = [name for name, _ in routine.items()]
    removable_test_names = []
    current_found = False
    for name in test_names:
        if name == session.test_number:
            current_found = True
        if current_found:
            removable_test_names.append(name)
    previously_tested_parameters = session.previously_tested_parameters
    for previous_test, _ in session.previously_tested_parameters.items():
        if previous_test in removable_test_names:
            del previously_tested_parameters[previous_test]
            session.delete_previous_test(previous_test)
    session._previously_tested_parameters = json.dumps(previously_tested_parameters)
    session.save()

    return redirect('session_detail', pk=pk)


@login_required
def test_switch(request, pk, number):
    session = Session.objects.get(pk=pk)
    session.test_number = number
    session.save()
    return redirect('session_detail', pk=pk)


@login_required
def next_test_switch(request, pk, priority: str):
    session = Session.objects.get(pk=pk)
    routine = api_client.get_routine()

    test_names = [name for name, _ in routine.items()]

    next_test = None
    next_primary_test = None

    current_found = False
    for i, test_info in enumerate(routine.items()):
        if current_found:
            if test_info[1]["priority"] == "primary":
                next_primary_test = test_names[i]
                break
        if test_info[0] == session.test_number:
            next_test = test_names[i+1]
            current_found = True

    if priority == "primary":
        session.test_number = next_primary_test
    elif priority == "any":
        session.test_number = next_test

    session.clean_min_max()
    session.save()
    return redirect('session_detail', pk=pk)


@login_required
def serve_gcode(request, pk):
    session = Session.objects.get(pk=pk)
    response = FileResponse(session.get_gcode, content_type='text/plain')
    response['Content-Type'] = 'text/plain'
    response['Content-Disposition'] = 'attachment; filename={}.gcode'.format(session.name.replace(" ", "_") + "_" + session.test_number)
    return response


class SessionUpdateView(LoginRequiredMixin, generic.UpdateView):
    template_name = 'session/session.html'
    form_class = SettingForm
    model = Session

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['percentage_complete'] = 100 / optimizer_info.length * int(self.object.test_number)
        context['executed'] = False
        return context

    def form_valid(self, form):
        settings = form.save(commit=False)
        # Do any custom stuff here
        settings.save()
        self.get_context_data()['executed'] = True
        return redirect('session_detail', pk=settings.pk)


@login_required
def faq(request):
    context = {}
    return render(request, 'session/faq.html', context)


@login_required
def quick_start(request):
    context = {}
    return render(request, 'session/quick_start.html', context)


@login_required
def support(request):
    context = {}
    return render(request, 'session/support.html', context)

@login_required
def guide(request):

    return FileResponse(open(finders.find('session/doc/manual.pdf'), 'rb'), content_type='application/pdf')


@login_required
def new_session(request):
    if request.method == 'POST':
        form = SessionForm(request.POST)

        if form.is_valid():
            messages.success(request, 'The session has been created!')
            session = form.save(commit=False)
            session.owner = request.user

            session.settings = Settings.objects.create(name=session.name)

            session._persistence = json.dumps(api_client.get_template())
            session.init_settings()
            session.update_persistence()

            session.save()
            return redirect('session_detail', pk=session.pk)
    else:
        form = SessionForm()

    context = {"form": form, "target_descriptions": load_json('session/json/target_descriptions.json')}
    return render(request, 'session/new_session.html', context)


@login_required
def testing_session(request):
    target_descriptions = load_json("session/json/target_descriptions.json")
    print(target_descriptions)
    context = {"target_descriptions": target_descriptions}
    return render(request, 'session/testing_session.html', context)


@login_required
def session_json(request, pk):
    if request.method == "GET":
        session = Session.objects.get(pk=pk)
        context = {"json": json.dumps(session.persistence, indent=4)}
        return render(request, "session/json.html", context=context)
