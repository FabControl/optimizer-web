from django.contrib.auth import views as auth_views
import simplejson as json
from django.http import HttpResponse
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash, get_user_model
from django.utils.datastructures import MultiValueDictKeyError
from .forms import SignUpForm, ResetPasswordForm
from django.views import generic
from django.views.generic.edit import FormView, ModelFormMixin, ProcessFormView
from django.utils.decorators import method_decorator
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.csrf import csrf_protect
from django.utils.safestring import mark_safe
from django.contrib import messages
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Div
from django.contrib.auth.decorators import login_required
from django.utils.datastructures import MultiValueDictKeyError
from django.urls import reverse_lazy, reverse
from django.shortcuts import render, redirect
from .forms import ResetPasswordForm, SignUpForm, LoginForm, ChangePasswordForm, LegalInformationForm
from .tokens import account_activation_token, affiliate_token_generator
from django.utils.encoding import force_text, force_bytes
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from messaging import email
from django.contrib.auth.tokens import default_token_generator
from .models import Affiliate
from django.contrib.auth.mixins import LoginRequiredMixin


# Create your views here.
def user_login(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
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
                    messages.error(request, "Your account has been deactivated.")
                    return render(request, 'authentication/login.html', {'form': LoginForm()})
            else:
                messages.error(request, "Failed to log in!")
                return redirect("login")
        else:
            print(form.errors)
            messages.error(request, "Failed to log in!")
            return render(request, 'authentication/login.html', {'form': LoginForm(), 'form_errors': form.errors})
    else:
        return render(request, 'authentication/login.html', {'form': LoginForm()})


def user_signup(request):
    context = {"form": SignUpForm}
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save_and_notify(request)
            return render(request, 'authentication/check_email.html', context)
        else:
            known_email = 'Email must be unique'
            form_errors = list(filter(lambda x: x != known_email,
                (str(m.as_text()).lstrip('* ') for m in dict(form.errors).values())))
            if len(form_errors) < 1:
                # someone is attempting to register twice with same email
                # or checking if account with email exists
                user_email = request.POST['email'].strip()
                user = get_user_model().objects.get(email=user_email)
                email.send_to_single(user_email, 'register_with_known_email',
                                     request,
                                     receiving_user=' '.join((user.first_name, user.last_name)),
                                     token=default_token_generator.make_token(user),
                                     uid=urlsafe_base64_encode(force_bytes(user.pk))
                                     )
                return render(request, 'authentication/check_email.html', context)


            message = "<br>".join(form_errors)
            messages.error(request, mark_safe(message))
    return render(request, 'authentication/signup.html', context)


@login_required
def onboarding_toggler(request):
    if request.method == "POST":
        try:
            sections = request.POST["section"]
        except MultiValueDictKeyError:
            sections = request.POST["section[]"]
        if type(sections) != list:
            sections = [sections]
        mode = request.POST["mode"]
        user = request.user
        temp_sections = user.onboarding_sections

        result = {'success': True, 'section_added': [], 'section_removed': []}

        if mode == 'true':
            for section in sections:
                if section not in user.onboarding_sections:
                    temp_sections.append(section)
                    result["section_added"].append(section)
        else:
            for section in sections:
                if section in user.onboarding_sections:
                    temp_sections.remove(section)
                    result["section_removed"].append(section)

        user.onboarding_sections = temp_sections
        user.save()
        return HttpResponse(result, content_type='application/json')


@login_required
def onboarding_disable(request):
    path = reverse_lazy("dashboard")
    if "next" in request.GET:
        path = request.GET["next"]
    user = request.user
    user.onboarding = False
    user.save()
    result = {"success": True}
    return HttpResponse(json.dumps(result), content_type='application/json')


@login_required
def onboarding_reset(request):
    user = request.user
    user.onboarding_reset()


@login_required
def user_logout(request):
    logout(request)
    return redirect("login")


def password_reset(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = ResetPasswordForm(request.POST)
        if form.is_valid():
            form.save(request=request)
            return redirect('password_reset_done')

    return render(request, 'authentication/password_reset.html', {'form': ResetPasswordForm})

class PasswordChangeView(auth_views.PasswordContextMixin, FormView):
    template_name='authentication/password_change.html'
    form_class=ChangePasswordForm
    success_url = reverse_lazy('index')
    title = ''

    @method_decorator(sensitive_post_parameters())
    @method_decorator(csrf_protect)
    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.save()
        # Updating the password logs out all other sessions for the user
        # except the current one.
        update_session_auth_hash(self.request, form.user)
        messages.success(self.request, 'Password changed')
        return super().form_valid(form)

def activate_account(request, uidb64, token):
    u_model = get_user_model()
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = u_model.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, u_model.DoesNotExist):
        user = None

    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        affiliates = Affiliate.objects.filter(receiver=user)
        if len(affiliates) > 0:
            affiliates[0].confirm(request)

        login(request, user)
        messages.success(request, 'Your email address was confirmed and account activated.')
        return redirect('dashboard')

    return render(request, 'authentication/invalid_activation_link.html')

class MyAffiliatesView(LoginRequiredMixin, ModelFormMixin, generic.ListView, ProcessFormView):
    object = None
    model = Affiliate
    fields = ('email', 'name', 'message')
    template_name = 'authentication/my_affiliates.html'
    success_url = reverse_lazy('my_affiliates')

    def get_queryset(self):
        return Affiliate.objects.filter(sender=self.request.user).order_by('date_created').reverse()[:100]

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form_clean = form.clean

        def clean():
            form_clean()
            mail = form.cleaned_data['email']
            if len(get_user_model().objects.filter(email=mail)) > 0 or len(Affiliate.objects.filter(email=mail)) > 0:
                form.add_error('email', 'User already invited or registered')

        form.clean = clean

        form.fields['message'].widget.attrs['rows'] = 5

        form.helper = FormHelper()
        form.helper.add_input(Submit('submit', 'Send', css_class='btn btn-primary'))
        form.helper.method = 'POST'
        form.helper.layout = Layout(Div(Div(Div('email', 'name', css_class='col'),
                                            Div('message', css_class='col'), 
                                            css_class='row'),
                                        css_class='container'))
        return form

    def form_valid(self, form):
        affiliate = form.save(commit=False)
        affiliate.sender = self.request.user

        affiliate.save()
        email.send_to_single(affiliate.email, 'affiliate_invitation', self.request,
                            affiliate=affiliate,
                            uid=urlsafe_base64_encode(force_bytes(affiliate.pk)),
                            token=affiliate_token_generator.make_token(affiliate))

        messages.success(self.request, 'Invitation sent to {0.name} ({0.email})'.format(affiliate))
        # send invitation message
        return redirect('my_affiliates')

    def form_invalid(self, form):
        self.object_list = self.get_queryset()
        return super().form_invalid(form)


def use_affiliate(request, uidb64, token):
    if request.user.is_authenticated:
        return redirect('dashboard')
    try:
        affiliate = Affiliate.objects.get(pk=force_text(urlsafe_base64_decode(uidb64)))
    except(TypeError, ValueError, OverflowError, Affiliate.DoesNotExist):
        affiliate = None

    if (affiliate is not None and
        affiliate_token_generator.check_token(affiliate, token) and
        len(get_user_model().objects.filter(email=affiliate.email)) == 0):

        if request.method == 'POST':
            form = SignUpForm(request.POST)
            if form.is_valid():
                if form.cleaned_data['email'] == affiliate.email:
                    new_user = form.save(commit=False)
                    new_user.is_active = True
                    new_user.save()
                    affiliate.receiver = new_user
                    affiliate.confirm(request)
                    login(request, new_user)
                    return redirect('dashboard')

                else:
                    new_user = form.save_and_notify(request)
                    affiliate.receiver = new_user
                    affiliate.save()
                    return render(request, 'authentication/check_email.html', {})

            else:
                form_errors = [str(m.as_text()).lstrip('* ') for m in dict(form.errors).values()]
                messages.error(request, '<br>'.join(form_errors))

        else:
            form = SignUpForm(initial=dict(email=affiliate.email, first_name=affiliate.name))

        return render(request, 'authentication/signup.html', dict(form=form))

    return render(request, 'authentication/invalid_affiliate_url.html')


@login_required
def legal_information_view(request):
    if request.method == 'POST':
        form = LegalInformationForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save(commit=True)
            messages.success(request, 'Account changed successfully')
            return redirect(reverse('dashboard'))
        else:
            form_errors = (str(m.as_text()).lstrip('* ') for m in dict(form.errors).values())
            message = "<br>".join(form_errors)
            messages.error(request, mark_safe(message))

    else:
        form = LegalInformationForm(instance=request.user)
    return render(request,
                  'authentication/legal_info.html',
                  dict(legal_info=form))
