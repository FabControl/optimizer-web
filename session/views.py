from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.staticfiles import finders
from .utilities import load_json, optimizer_info
from django.http import FileResponse, HttpResponseRedirect, Http404, HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render_to_response

from .models import *
from django.views import generic
from .forms import *

from config import config
from optimizer_api import api_client

# Create your views here.


def index(request):
    return redirect('dashboard')
    # raise Http404("Page not found")


@login_required
def dashboard(request):
    latest_sessions = Session.objects.filter(owner=request.user).order_by('pk')[:5]
    context = {'latest_sessions': latest_sessions}
    return render(request, 'session/dashboard.html', context)


@login_required
def material_detail(request, name):
    material = get_object_or_404(Material, name=name)
    context = {'material': material,
               'someinfo': "someinfo"}
    return render(request, 'session/material.html', context)


class MaterialsView(LoginRequiredMixin, generic.ListView):
    template_name = "session/material_manager.html"
    context_object_name = 'materials'

    def get_queryset(self):
        queryset = Material.objects.filter(owner=self.request.user).order_by('pub_date')
        return queryset


class MaterialView(LoginRequiredMixin, generic.UpdateView):
    model = Material
    template_name = 'session/material_form.html'
    form_class = MaterialForm
    success_url = reverse_lazy("material_manager")

    def __init__(self):
        super(MaterialView, self).__init__()

    def get_context_data(self, **kwargs):
        material = self.object
        material.is_owner(self.request.user)
        context = super(MaterialView, self).get_context_data(**kwargs)
        return context


@login_required
def material_form(request):
    context = {}
    if request.method == 'POST':
        form = MaterialForm(request.POST)
        if form.is_valid():
            material = form.save(commit=False)
            material.owner = request.user
            messages.success(request, 'Material "{}" has been created!'.format(material.name))
            material.save()
            if "next" in request.POST:
                request.session["material"] = material.pk
                return redirect(request.POST["next"])
            else:
                return redirect("material_manager")
    else:
        form = MaterialForm()
        if "next" in request.GET:
            context["next"] = request.GET["next"]
    context["form"] = form
    return render(request, 'session/material_form.html', context)


@login_required
def machine_edit_view(request, pk):
    context = {}
    machine = get_object_or_404(Machine, pk=pk)
    if request.method == 'POST':
        self_form = NewMachineForm(request.POST, instance=machine)
        extruder_form = NewExtruderForm(request.POST, instance=machine.extruder)
        nozzle_form = NewNozzleForm(request.POST, instance=machine.extruder.nozzle)
        chamber_form = NewChamberForm(request.POST, instance=machine.chamber)
        printbed_form = NewPrintbedForm(request.POST, instance=machine.printbed)
        extruder = None
        if self_form.is_valid():
            machine = self_form.save(commit=False)
            machine.owner = request.user
            if extruder_form.is_valid():
                extruder = extruder_form.save(commit=False)
                extruder.nozzle = nozzle_form.save()
                extruder.save()
            if chamber_form.is_valid():
                machine.chamber = chamber_form.save()
            if printbed_form.is_valid():
                machine.printbed = printbed_form.save()
            messages.success(request, '{} has been updated!'.format(machine.model))
            machine.extruder = extruder
            machine.save()
            if "next" in request.POST:
                request.session["machine"] = machine.pk
                return redirect(request.POST["next"])
            else:
                return redirect('machine_manager')
    else:
        self_form = NewMachineForm(instance=machine)
        if "next" in request.GET:
            context["next"] = request.GET["next"]
        extruder_form = NewExtruderForm(instance=machine.extruder)
        nozzle_form = NewNozzleForm(instance=machine.extruder.nozzle)
        chamber_form = NewChamberForm(instance=machine.chamber)
        printbed_form = NewPrintbedForm(instance=machine.printbed)
    form_context = {"self_form": self_form,
                    "extruder_form": extruder_form,
                    "nozzle_form": nozzle_form,
                    "chamber_form": chamber_form,
                    "printbed_form": printbed_form}
    context = {**context, **form_context}
    return render(request, 'session/machine_form.html', context)


class MachineView(LoginRequiredMixin, generic.UpdateView):
    form_class = NewMachineForm
    model = Machine
    template_name = 'session/machine_detail.html'

    def get_context_data(self, **kwargs):
        machine = self.object
        machine.is_owner(self.request.user)
        context = super(MachineView, self).get_context_data(**kwargs)
        return context


class MachinesView(LoginRequiredMixin, generic.ListView):
    template_name = "session/machine_manager.html"
    context_object_name = 'machines'

    def get_queryset(self):
        queryset = Machine.objects.filter(owner=self.request.user).order_by('pub_date')
        return queryset


@login_required
def machine_form(request):
    context = {}
    if request.method == 'POST':
        self_form = NewMachineForm(request.POST)
        extruder_form = NewExtruderForm(request.POST)
        nozzle_form = NewNozzleForm(request.POST)
        chamber_form = NewChamberForm(request.POST)
        printbed_form = NewPrintbedForm(request.POST)
        extruder = None
        if self_form.is_valid():
            machine = self_form.save(commit=False)
            machine.owner = request.user
            if extruder_form.is_valid():
                extruder = extruder_form.save(commit=False)
                extruder.nozzle = nozzle_form.save()
                extruder.save()
            if chamber_form.is_valid():
                machine.chamber = chamber_form.save()
            if printbed_form.is_valid():
                machine.printbed = printbed_form.save()
            messages.info(request, 'Machine "{}" has been created!'.format(machine.model))
            machine.extruder = extruder
            machine.save()
            if "next" in request.POST:
                request.session["machine"] = machine.pk
                return redirect(request.POST["next"])
            else:
                return redirect('machine_manager')
    else:
        self_form = NewMachineForm()
        if "next" in request.GET:
            context["next"] = request.GET["next"]
        extruder_form = NewExtruderForm()
        nozzle_form = NewNozzleForm()
        chamber_form = NewChamberForm()
        printbed_form = NewPrintbedForm()
    form_context = {"self_form": self_form,
               "extruder_form": extruder_form,
               "nozzle_form": nozzle_form,
               "chamber_form": chamber_form,
               "printbed_form": printbed_form}
    context = {**context, **form_context}
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
        logging.getLogger("views").info("New session form valid!")
        # Do any custom stuff here
        session.persistence = api_client.return_data(session.persistence, "persistence")
        session.update_test_info()
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
        session = form.save(commit=False)
        return redirect('session_validate_back', pk=session.pk)


class SessionOverview(LoginRequiredMixin, generic.DetailView):
    model = Session
    template_name = "session/session.html"

    def get_context_data(self, **kwargs):
        session = self.object
        session.is_owner(self.request.user)
        context = super().get_context_data(**kwargs)
        context['routine'] = api_client.get_routine()
        return context


@login_required
def generate_or_validate(request, pk):
    session = get_object_or_404(Session, pk=pk)
    session.is_owner(request.user)

    # Check if user still is onboarding
    if request.user.onboarding:
        if session.test_number not in ["01", "03"]:
            request.user.onboarding = False
            request.user.save()
    
    if session.executed:
        logging.getLogger("views").info("{} is initializing Session validation view!".format(request.user))
        return SessionValidateView.as_view()(request, pk=pk)
    else:
        logging.getLogger("views").info("{} is initializing Session generation view!".format(request.user))
        return SessionView.as_view()(request, pk=pk)


class SessionDelete(LoginRequiredMixin, generic.DeleteView):
    model = Session
    success_url = reverse_lazy('session_manager')

    def delete(self, request, *args, **kwargs):
        """
        Call the delete() method on the fetched object and then redirect to the
        success URL.
        """
        if Session.objects.get(pk=self.kwargs["pk"]).owner != self.request.user:
            raise Exception('Session not owned by user.')
        self.object = self.get_object()
        success_url = self.get_success_url()
        self.object.delete()
        return HttpResponseRedirect(success_url)


class MachineDelete(LoginRequiredMixin, generic.DeleteView):
    model = Machine
    success_url = reverse_lazy('machine_manager')

    def delete(self, request, *args, **kwargs):
        """
        Call the delete() method on the fetched object and then redirect to the
        success URL.
        """
        if Machine.objects.get(pk=self.kwargs["pk"]).owner != self.request.user:
            raise Exception('Machine not owned by user.')
        self.object = self.get_object()
        success_url = self.get_success_url()
        self.object.delete()
        return HttpResponseRedirect(success_url)


class MaterialDelete(LoginRequiredMixin, generic.DeleteView):
    model = Material
    success_url = reverse_lazy('material_manager')

    def delete(self, request, *args, **kwargs):
        """
        Call the delete() method on the fetched object and then redirect to the
        success URL.
        """
        if Material.objects.get(pk=self.kwargs["pk"]).owner != self.request.user:
            raise Exception('Material not owned by user.')
        self.object = self.get_object()
        success_url = self.get_success_url()
        self.object.delete()
        return HttpResponseRedirect(success_url)


@login_required
def session_validate_undo(request, pk):
    session = Session.objects.get(pk=pk)
    session.is_owner(request.user)
    session.remove_last_test()

    previously_tested_parameters = session.previously_tested_parameters
    del previously_tested_parameters[session.test_number]
    session._previously_tested_parameters = json.dumps(previously_tested_parameters)
    session.save()

    return redirect('session_detail', pk=pk)


@login_required
def session_validate_revert(request, pk):
    session = Session.objects.get(pk=pk)
    session.is_owner(request.user)

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
    session.is_owner(request.user)
    session.test_number = number
    session.save()
    return redirect('session_detail', pk=pk)


@login_required
def next_test_switch(request, pk, priority: str):
    session = get_object_or_404(Session, pk=pk)
    session.is_owner(request.user)
    if priority == "primary":
        session.test_number = session.test_number_next()
    elif priority == "any":
        session.test_number = session.test_number_next(primary=False)
    session.clean_min_max()
    session.save()
    return redirect('session_detail', pk=pk)


@login_required
def serve_gcode(request, pk):
    session = Session.objects.get(pk=pk)
    session.is_owner(request.user)
    response = FileResponse(session.get_gcode, content_type='text/plain')
    response['Content-Type'] = 'text/plain'
    response['Content-Disposition'] = 'attachment; filename={}.gcode'.format(session.name.replace(" ", "_") + "_" + session.test_number)
    return response


@login_required
def serve_config(request, pk, slicer):
    supported_slicers = ["simplify3d", "slic3r_pe", 'cura']
    assert slicer in supported_slicers
    session = get_object_or_404(Session, pk=pk)
    session.is_owner(request.user)
    configuration_file, configuration_file_format = api_client.get_config(slicer, session.persistence)
    response = FileResponse(configuration_file.decode(encoding = "ISO-8859-1"), content_type='text/plain')
    response['Content-Type'] = 'text/xml'
    response['Content-Disposition'] = 'attachment; ' + 'filename={}_{}'.format(str(session.material), str(session.machine)).replace(" ", "_").replace(".", "-") + '.{}'.format(configuration_file_format)
    return response


@login_required
def serve_report(request, pk):
    from io import BytesIO
    session = get_object_or_404(Session, pk=pk)
    session.is_owner(request.user)
    report_file, report_file_format = api_client.get_report(session.persistence)
    f = BytesIO(report_file)
    response = FileResponse(f, content_type='application/pdf')
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


def terms_of_use(request):
    return FileResponse(open(finders.find('session/doc/3doptimizer_TU.pdf'), 'rb'), content_type='application/pdf')


@login_required
def new_session(request):
    if request.method == 'POST':
        form = SessionForm(request.POST, user=request.user)

        if form.is_valid():
            session = form.save(commit=False)
            session.owner = request.user

            session.settings = Settings.objects.create(name=session.name)

            session._persistence = json.dumps(api_client.get_template())
            session.init_settings()
            session.update_persistence()

            session.save()
            return redirect('session_detail', pk=session.pk)
    else:
        form = SessionForm(user=request.user)
        if "machine" in request.session:
            form.fields["machine"].initial = request.session["machine"]

        if "material" in request.session:
            form.fields["material"].initial = request.session["material"]

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
    if not request.user.is_staff:
        raise Http404()
    if request.method == "GET":
        session = Session.objects.get(pk=pk)
        context = {"json": json.dumps(session.persistence, indent=4)}
        return render(request, "session/json.html", context=context)


@login_required
def session_test_info(request, pk):
    if not request.user.is_staff:
        raise Http404()
    if request.method == "GET":
        session = Session.objects.get(pk=pk)
        context = {"test_info": json.dumps(session.test_info, indent=4)}
        return render(request, "session/test_info.html", context=context)


def session_health_check(request):
    resp = api_client.get_template()
    if resp is not None:
        return HttpResponse('')
    raise Http404()

def error_404_view(request, exception):
    response = render_to_response('session/404.html', {"user": request.user})
    response.status_code = 404
    return response


def error_500_view(request):
    response = render_to_response('session/500.html', {"user": request.user})
    response.status_code = 500
    return response
