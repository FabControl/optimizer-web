from django.contrib.auth import views as auth_views
import simplejson as json
from django.http import HttpResponse
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash, get_user_model
from django.utils.datastructures import MultiValueDictKeyError
from .forms import SignUpForm, ResetPasswordForm
from django.views import generic
from django.views.generic.edit import FormView
from django.utils.decorators import method_decorator
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.csrf import csrf_protect
from django.utils.safestring import mark_safe
from django.contrib import messages

from django.contrib.auth.decorators import login_required
from django.utils.datastructures import MultiValueDictKeyError
from django.urls import reverse_lazy, reverse
from django.shortcuts import render, redirect
from .forms import ResetPasswordForm, SignUpForm, LoginForm, ChangePasswordForm, LegalInformationForm
from .tokens import account_activation_token
from django.utils.encoding import force_text, force_bytes
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from messaging import email
from django.contrib.auth.tokens import default_token_generator


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
        login(request, user)
        messages.success(request, 'Your email address was confirmed and account activated.')
        return redirect('dashboard')

    return render(request, 'authentication/invalid_activation_link.html')

@login_required
def legal_information_view(request):
    if request.method == 'POST':
        form = LegalInformationForm(request.POST)
        if form.is_valid():
            form.save(request.user)
            return redirect(reverse('dashboard'))
        else:
            form_errors = (str(m.as_text()).lstrip('* ') for m in dict(form.errors).values())
            message = "<br>".join(form_errors)
            messages.error(request, mark_safe(message))

    else:
        user = request.user
        form = LegalInformationForm(dict(first_name=user.first_name,
                                        last_name=user.last_name))
    return render(request,
                  'authentication/legal_info.html',
                  dict(legal_info=form))
