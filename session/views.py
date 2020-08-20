from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.staticfiles import finders
from .utilities import load_json, optimizer_info, common_cura_qulity_types
from django.http import FileResponse, HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render_to_response, reverse
from django.contrib.auth import get_user_model
from django.forms.models import model_to_dict
from django.db.models import Q, Count, Max
from django.utils.translation import gettext as _
from django.urls import reverse_lazy

from .models import *
from django.views import generic
from .forms import *
from payments.models import Checkout, Corporation

from payments.forms import VoucherRedeemForm

from config import config
from optimizer_api import api_client
from datetime import timedelta


def model_ownership_query(user):
    if user.member_of_corporation is None:
        # if user leaves corporation, he des not see resources he created within corp.
        return Q(owner=user) & Q(corporation=None)
    return (Q(owner=user) |
            (Q(corporation=user.member_of_corporation) & Q(owner__in=user.member_of_corporation.team.all())))


class ModelOwnershipCheckMixin:
    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(model_ownership_query(self.request.user))

# Create your views here.


def index(request):
    return redirect('dashboard')
    # raise Http404("Page not found")


@login_required
def dashboard(request):
    user = request.user
    latest_sessions = user.session_set.filter(Q(corporation=None) | Q(corporation=user.member_of_corporation)).order_by('-pub_date')[:5]

    ownership = model_ownership_query(user)
    #TODO optimize this to use sigle query and only return counts
    len_printers = len(Machine.objects.filter(ownership))
    len_materials = len(Material.objects.filter(ownership))
    len_sessions = len(Session.objects.filter(ownership))

    cards = {'printers': {'len': len_printers},
             'materials': {'len': len_materials},
             'sessions': {'len': len_sessions}}
    # Team members if user in a team
    if request.user.member_of_corporation:
        cards['corporation'] = {'len': len(request.user.member_of_corporation.team_sorted)}

    context = {'latest_sessions': latest_sessions,
               'invitations': Corporation.objects.filter(_invited_users__contains=' '+ user.email + ' '),
               'cards': cards,
               'voucher_form': VoucherRedeemForm()}
    return render(request, 'session/dashboard.html', context)


class MaterialsView(LoginRequiredMixin, ModelOwnershipCheckMixin, generic.ListView):
    template_name = "session/material_manager.html"
    context_object_name = 'materials'
    model = Material

    def get_queryset(self):
        return super().get_queryset().order_by('pub_date')


class MaterialView(LoginRequiredMixin, ModelOwnershipCheckMixin, generic.UpdateView):
    model = Material
    template_name = 'session/material_detail.html'
    form_class = MaterialForm
    success_url = reverse_lazy("material_manager")

    def __init__(self):
        super(MaterialView, self).__init__()


@login_required
def material_form(request):
    context = {}
    if request.method == 'POST':
        form = MaterialForm(request.POST)
        if form.is_valid():
            material = form.save(commit=False)
            material.owner = request.user
            material.corporation = request.user.member_of_corporation
            messages.success(request, _('Material "{material}" has been created!').format(material=material.name))
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
    machine = get_object_or_404(Machine, model_ownership_query(request.user), pk=pk)

    if request.method == 'POST':
        self_form = NewMachineForm(request.POST, instance=machine)
        extruder_form = NewExtruderForm(request.POST, instance=machine.extruder, prefix="extruder")
        nozzle_form = NewNozzleForm(request.POST, instance=machine.extruder.nozzle, prefix="nozzle")
        chamber_form = NewChamberForm(request.POST, instance=machine.chamber, prefix="chamber")
        printbed_form = NewPrintbedForm(request.POST, instance=machine.printbed, prefix="printbed")
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
            messages.success(request, _('{printer} has been updated!').format(printer=machine.model))
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
        extruder_form = NewExtruderForm(instance=machine.extruder, prefix="extruder")
        nozzle_form = NewNozzleForm(instance=machine.extruder.nozzle, prefix="nozzle")
        chamber_form = NewChamberForm(instance=machine.chamber, prefix="chamber")
        printbed_form = NewPrintbedForm(instance=machine.printbed, prefix="printbed")
    form_context = {"self_form": self_form,
                    "extruder_form": extruder_form,
                    "nozzle_form": nozzle_form,
                    "chamber_form": chamber_form,
                    "printbed_form": printbed_form}
    context = {**context, **form_context}
    return render(request, 'session/machine_detail.html', context)


class MachinesView(LoginRequiredMixin, ModelOwnershipCheckMixin, generic.ListView):
    template_name = "session/machine_manager.html"
    context_object_name = 'machines'
    model = Machine

    def get_queryset(self):
        return super().get_queryset().order_by('pub_date')


@login_required
def machine_form(request):
    context = {}
    if request.method == 'POST':
        self_form = NewMachineForm(request.POST)
        extruder_form = NewExtruderForm(request.POST, prefix="extruder")
        nozzle_form = NewNozzleForm(request.POST, prefix="nozzle")
        chamber_form = NewChamberForm(request.POST, prefix="chamber")
        printbed_form = NewPrintbedForm(request.POST, prefix="printbed")
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
            messages.success(request, _('3D Printer "{printer}" has been created!').format(printer=machine.model))
            machine.extruder = extruder
            machine.corporation = request.user.member_of_corporation
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
        extruder_form = NewExtruderForm(prefix="extruder")
        nozzle_form = NewNozzleForm(prefix="nozzle")
        chamber_form = NewChamberForm(prefix="chamber")
        printbed_form = NewPrintbedForm(prefix="printbed")

    form_context = {"self_form": self_form,
               "extruder_form": extruder_form,
               "nozzle_form": nozzle_form,
               "chamber_form": chamber_form,
               "printbed_form": printbed_form}

    sample_machines = Machine.objects.filter(owner=get_user_model().objects.get(email=settings.SAMPLE_SESSIONS_OWNER)).order_by('model')
    context = {'sample_machines': sample_machines, **context, **form_context}
    return render(request, 'session/machine_form.html', context)

@login_required
def sample_machine_data(request, pk):
    owner = get_user_model().objects.get(email=settings.SAMPLE_SESSIONS_OWNER)
    machine = get_object_or_404(Machine, pk=pk, owner=owner)
    result = model_to_dict(machine, NewMachineForm.Meta.fields)

    subforms = ((machine.extruder, NewExtruderForm, 'extruder'),
                (machine.extruder.nozzle, NewNozzleForm, 'nozzle'),
                (machine.chamber, NewChamberForm, 'chamber'),
                (machine.printbed, NewPrintbedForm, 'printbed'))

    for i, t, p in subforms:
        for k, v in model_to_dict(i, t.Meta.fields).items():
            result[p + '-' + k] = v
    return JsonResponse(result)


class SessionListView(LoginRequiredMixin, ModelOwnershipCheckMixin, generic.ListView):
    template_name = "session/session_manager.html"
    context_object_name = 'sessions'
    model = Session

    def get_queryset(self):
        return super().get_queryset().order_by('pub_date')


class SessionTestsSelectionMixin:
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        routine = api_client.get_routine()
        for (k, v) in routine.items():
            v['free'] = True if k in settings.FREE_TESTS else False
            v['name'] = v['name'].title().replace(' Vs ', ' vs<br>')
            v['name'] = f'{int(k)}. {_(v["name"])}'
        routine = {r: routine[r] for r in self.object.mode.included_tests}
        context['routine'] = routine
        return context

# include these in auto-generated translation files, but always retrieve from backend
if False:
    _("Z-Offset")
    _("First-Layer Track Height vs<br>First-Layer Printing Speed")
    _("First-Layer Track Width")
    _("Extrusion Temperature vs<br>Printing Speed")
    _("Track Height vs<br>Printing Speed")
    _("Track Width")
    _("Extrusion Multiplier")
    _("Printing Speed")
    _("Extrusion Temperature vs<br>Retraction Distance")
    _("Retraction Distance vs<br>Printing Speed")
    _("Retraction Distance")
    _("Retraction Distance vs<br>Retraction Speed")
    _("Retraction Restart Distance vs<br>Printing Speed And Coasting Distance")
    _("Bridging Extrusion Multiplier vs<br>Bridging Printing Speed")

class SessionView(SessionTestsSelectionMixin, LoginRequiredMixin, generic.UpdateView):
    model = Session
    form_class = TestGenerateForm
    template_name = 'session/session.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['rename_form'] = SessionRenameForm(instance=self.object)
        context['offer_download'] = self.kwargs.get('download', 1)
        return context

    def form_valid(self, form):
        session = form.save(commit=False)
        logging.getLogger("views").info("New session form valid!")
        # Do any custom stuff here
        session.persistence = api_client.return_data(session.persistence, "persistence")
        session.update_test_info()
        session.save()
        return redirect('session_detail', pk=session.pk)


class GuidedSessionView(SessionView):
    template_name = 'session/guided_mode/guided_session.html'


class SessionValidateView(SessionView):
    form_class = TestValidateForm

    def form_valid(self, form):
        session = form.save(commit=False)
        session.alter_previous_tests(-1, "validated", True)
        session = form.save(commit=True)
        if self.request.method == "POST" and "btnprimary" in self.request.POST:
            return redirect('session_next_test', pk=session.pk, priority="any")
        else:
            return redirect('session_next_test', pk=session.pk, priority="any")

    def form_invalid(self, form):
        session = form.save(commit=False)
        return redirect('session_validate_back', pk=session.pk)


class GuidedValidateView(GuidedSessionView):
    form_class = TestValidateForm

    def get_context_data(self, **kwargs):
        session = self.object
        context = super().get_context_data(**kwargs)
        context['question_form'] = ValidateFormTestDescriptionForm(instance=self.object)
        context['questions'] = Junction.objects.get(base_test=session.test_number).descriptors.all()
        return context

    def form_valid(self, form):
        session = form.save(commit=False)
        session.alter_previous_tests(-1, "validated", True)
        session = form.save(commit=True)
        # filter any items in request.POST with key that starts with 'question' and has any value other than 'null'
        questions = [PrintDescriptor.objects.get(pk=int(y)) for y in [self.request.POST[x] for x in self.request.POST if x.startswith('question')] if y != 'null']
        # sort the selected questions by target tests as numbers.
        questions.sort(key=lambda x: int(x.target_test))
        if len(questions) > 0:
            # Select the highest priority test. Lower test number = higher priority
            # first element will have the lowest test number
            q1 = questions[0]
            if q1.hint is not None:
                messages.info(self.request, q1.hint)
            if q1.target_test == session.test_number:
                session.delete_previous_test(q1.target_test)
                session.save()
            return redirect('test_switch', number=q1.target_test, pk=session.pk)
        # Go to next primary if not directed elsewhere
        return redirect('session_next_test', pk=session.pk, priority='primary')

    def form_invalid(self, form):
        session = form.save(commit=False)
        return redirect('session_validate_back', pk=session.pk)


class SessionOverview(SessionTestsSelectionMixin, LoginRequiredMixin, ModelOwnershipCheckMixin, generic.DetailView):
    model = Session
    template_name = "session/session_overview.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['default_quality_type'] = 'normal'
        context['other_quality_types'] = common_cura_qulity_types
        context['rename_form'] = SessionRenameForm(instance=self.object)
        return context


class GuidedSessionOverview(SessionOverview):
    template_name = 'session/session_overview.html'


@login_required
def overview_dispatcher(request, pk):
    session = get_object_or_404(Session, model_ownership_query(request.user), pk=pk)

    if session.mode.type == 'guided':
        return GuidedSessionOverview.as_view()(request, pk=pk)
    elif session.mode.type == 'normal':
        return SessionOverview.as_view()(request, pk=pk)


@login_required
def session_dispatcher(request, pk, download=1):
    session = get_object_or_404(Session, model_ownership_query(request.user), pk=pk)

    # Check if user still is onboarding
    if request.user.onboarding:
        if session.test_number not in ["01", "03"]:
            request.user.onboarding = False
            request.user.save()

    # Make sure that the user is not where they shouldn't be
    if session.test_number not in request.user.available_tests:
        next_test = session.test_number_next()
        if next_test not in request.user.available_tests:
            session.test_number = request.user.available_tests[-1]
            return overview_dispatcher(request, pk=pk)
        else:
            session.test_number = next_test
            corporation = request.user.member_of_corporation
            if corporation is None or corporation.owner == request.user:
                msg = _("Your next test is available in Full Access only. "
                        "You can skip it and go to the next available test or "
                        "<a href={link}>purchase Full Access.</a>").format(link=reverse('plans'))
            else:
                msg = _("Your next test is available in Full Access only. "
                        "You can skip it and go to the next available test or "
                        "ask {first_name} {last_name} to upgrade account."
                        ).format(first_name=corporation.owner.first_name, last_name=corporation.owner.last_name)
            messages.error(request, mark_safe(msg))
        session.save()

    if session.mode.type == 'normal':
        # Check if session should be in Generate or Validate state
        if session.executed:
            logging.getLogger("views").info("{} is initializing Session validation view!".format(request.user))
            return SessionValidateView.as_view()(request, pk=pk, download=download)
        else:
            logging.getLogger("views").info("{} is initializing Session generation view!".format(request.user))
            return SessionView.as_view()(request, pk=pk)

    elif session.mode.type == 'guided':
        if session.executed:
            logging.getLogger("views").info("{} is initializing Session validation view!".format(request.user))
            return GuidedValidateView.as_view()(request, pk=pk, download=download)
        else:
            logging.getLogger("views").info("{} is initializing Session generation view!".format(request.user))
            return GuidedSessionView.as_view()(request, pk=pk)


class SessionDelete(LoginRequiredMixin, ModelOwnershipCheckMixin, generic.DeleteView):
    model = Session
    success_url = reverse_lazy('session_manager')

    def get(self, request, *args, **kwargs):
        raise Http404("Page not found")


class MachineDelete(LoginRequiredMixin, ModelOwnershipCheckMixin, generic.DeleteView):
    model = Machine
    success_url = reverse_lazy('machine_manager')

    def get(self, request, *args, **kwargs):
        raise Http404("Page not found")


class MaterialDelete(LoginRequiredMixin, ModelOwnershipCheckMixin, generic.DeleteView):
    model = Material
    success_url = reverse_lazy('material_manager')

    def get(self, request, *args, **kwargs):
        raise Http404("Page not found")



@login_required
def session_undo(request, pk):
    session = get_object_or_404(Session, model_ownership_query(request.user), pk=pk)
    if session.previous_tests[-1]['validated']:
        session.alter_previous_tests(-1, "validated", False)
        session.test_number = session.previous_tests[-1]['test_number']
        return redirect('session_detail', pk=pk, download=0)

    else:
        session.delete_previous_test(session.test_number, delete_above=False)
        session.save()
        return redirect('session_detail', pk=pk)


@login_required
def session_validate_revert(request, pk):
    session = get_object_or_404(Session, model_ownership_query(request.user), pk=pk)
    session.delete_previous_test(session.test_number)
    session.save()

    return redirect('session_detail', pk=pk)


@login_required
def test_switch(request, pk, number):
    session = get_object_or_404(Session, model_ownership_query(request.user), pk=pk)
    session.test_number = number
    session.save()
    return redirect('session_detail', pk=pk)


@login_required
def next_test_switch(request, pk, priority: str):
    session = get_object_or_404(Session, model_ownership_query(request.user), pk=pk)
    num = session.test_number
    if priority == "primary":
        session.test_number = session.test_number_next()
    elif priority == "any":
        session.test_number = session.test_number_next(primary=False)
    if session.test_number == num:
        return redirect('session_overview', pk=pk)
    session.clean_min_max()
    session.save()
    return redirect('session_detail', pk=pk)


@login_required
def serve_gcode(request, pk):
    session = get_object_or_404(Session, model_ownership_query(request.user), pk=pk)
    content = session.get_gcode

    gcode_filename = f'{session.number}_{{}}_T{session.test_number}_V{session.gcode_download_count:02d}.gcode'
    session_name = session.name
    session_name_max_length = 39 - len(gcode_filename) + 2 # include curly braces in calculation
    if len(session_name) > session_name_max_length:
        session_name = session_name[:session_name_max_length]
    gcode_filename = gcode_filename.format(session_name)

    response = HttpResponse(content, content_type='text/plain')
    response['Content-Disposition'] = 'attachment; filename={}'.format(gcode_filename.replace(' ', '_'))
    return response


@login_required
def serve_config(request, pk, slicer):
    supported_slicers = ["simplify3d", "slic3r_pe", 'cura']
    assert slicer in supported_slicers
    session = get_object_or_404(Session, model_ownership_query(request.user), pk=pk)

    quality_type = ''
    if request.method == 'POST':
        quality_type = request.POST.get('quality_type', '')

    configuration_file, configuration_file_format = api_client.get_config(slicer, session.persistence, quality_type)
    response = HttpResponse(configuration_file, content_type='application/octet-stream')

    filename = f'{session.number}_{session.material}_{session.machine}'
    response['Content-Disposition'] = 'attachment; filename={}.{}'.format(filename.replace(' ', '_'), configuration_file_format)

    return response


@login_required
def serve_report(request, pk):
    from io import BytesIO
    session = get_object_or_404(Session, model_ownership_query(request.user), pk=pk)
    report_file, report_file_format = api_client.get_report(session.persistence)
    f = BytesIO(report_file)
    response = FileResponse(f, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=report_{}.pdf'.format(session.name.replace(" ", "_"))
    return response


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
    if request.user.plan == 'basic':
        return redirect(reverse('session_manager'))

    if request.method == 'POST':
        form = SessionForm(request.POST, ownership=model_ownership_query(request.user), user=request.user)

        if form.is_valid():
            session = form.save(commit=False)
            session.owner = request.user
            session.corporation = request.user.member_of_corporation

            session.settings = Settings.objects.create(name=session.name)

            session._persistence = json.dumps(api_client.get_template())
            session.init_settings()
            session.update_persistence()

            session.save()
            Session.generate_id_number(session)

            for k in ('machine', 'material', 'optimizer_session_name'):
                if k in request.session:
                    del request.session[k]
            return redirect('session_detail', pk=session.pk)

    if request.method == 'PATCH':
        request.session['optimizer_session_name'] = request.body.decode('utf-8')
        return HttpResponse(status=204)

    else:
        form = SessionForm(ownership=model_ownership_query(request.user), user=request.user)
        if "machine" in request.session:
            form.fields["machine"].initial = request.session["machine"]

        if "material" in request.session:
            form.fields["material"].initial = request.session["material"]
        if "optimizer_session_name" in request.session:
            form.fields["name"].initial = request.session["optimizer_session_name"]

    context = {"form": form, "target_descriptions": load_json('session/json/target_descriptions.json')}
    return render(request, 'session/new_session.html', context)


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


class TeamStatsView(LoginRequiredMixin, generic.ListView):
    template_name = "session/team_stats.html"
    context_object_name = 'team'

    def get_queryset(self):
        if self.request.user.member_of_corporation is None:
            raise Http404()

        corp = self.request.user.member_of_corporation
        now = timezone.now()

        ownership_filter = Q(session__corporation=corp)
        seven_days_filter = ownership_filter & Q(session__pub_date__gt=(now - timedelta(days=7)))
        thirty_days_filter = ownership_filter & Q(session__pub_date__gt=(now - timedelta(days=30)))
        ninety_days_filter = ownership_filter & Q(session__pub_date__gt=(now - timedelta(days=90)))

        result = self.request.user.member_of_corporation.team.annotate(
                latest_session=Max('session', filter=ownership_filter),
                tests_total=Count('session', filter=ownership_filter),
                tests_seven=Count('session', filter=seven_days_filter),
                tests_thirty=Count('session', filter=thirty_days_filter),
                tests_ninety=Count('session', filter=ninety_days_filter))

        # should be ok, since we iterate over items in template anyways
        for user in result:
            if user.latest_session is not None:
                user.latest_session = Session.objects.get(pk=user.latest_session)

        return result

@login_required
def privacy_statement(request):
    return render(request, 'session/TOP.html')


@login_required
def stats_view(request):
    """
    Needs to display the following information:
    Total accounts
    New accounts this week
    New accounts this month
    Total active accounts
    :param request:
    :return:
    """
    if request.user.can_access_investor_dashboard:
        stats = []
        stats.append({'label': 'Accounts', 'value': len(User.objects.all())})
        stats.append({'label': 'Active accounts', 'value': len(User.objects.filter(is_active=True))})
        stats.append({'label': 'Online today', 'value': len(User.objects.filter(last_active__gt=timezone.datetime.today() - timezone.timedelta(days=1)))-1})  # minus one to exclude self
        stats.append({'label': 'New accounts last 24 hours', 'value': len(User.objects.filter(date_joined__gt=timezone.datetime.today() - timezone.timedelta(days=1)))})
        stats.append({'label': 'New accounts last 7 days', 'value': len(User.objects.filter(date_joined__gt=timezone.datetime.today() - timezone.timedelta(days=7)))})
        stats.append({'label': 'New accounts last 30 days', 'value': len(User.objects.filter(date_joined__gt=timezone.datetime.today() - timezone.timedelta(days=30)))})
        # TODO Replace with the actual amount of non-expired premium accounts. Not yet replaced, because accounts have not yet been migrated to their appropriate plans
        stats.append({'label': 'Paid subscriptions', 'value': len([checkout for checkout in Checkout.objects.filter(created__gt=timezone.datetime.today() - timezone.timedelta(days=30), is_paid=True)])})
        income_30 = sum([checkout.payment_plan.price for checkout in Checkout.objects.filter(created__gt=timezone.datetime.today() - timezone.timedelta(days=30), is_paid=True)])
        stats.append({'label': 'Revenue last 30 days (EUR)', 'value': '{0},-'.format(int(income_30))})
        income_90 = sum([checkout.payment_plan.price for checkout in Checkout.objects.filter(created__gt=timezone.datetime.today() - timezone.timedelta(days=90), is_paid=True)])
        stats.append({'label': 'Revenue last 90 days (EUR)', 'value': '{0},-'.format(int(income_90))})

        return render(request, 'session/stats_dashboard.html', context={'stats': stats})
    else:
        raise Http404()


def terms_of_use(request):
    return render(request, 'session/TOS.html')


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

@login_required
def session_rename(request, pk):
    return_page = 'session_detail'
    if request.method == 'POST':
        SessionRenameForm(request.POST,
                        model_ownership_query(request.user),
                        instance=get_object_or_404(Session, pk=pk)).save()

        return_page = request.POST.get('return_page', return_page)

    return redirect(reverse(return_page, kwargs={'pk':pk}))
