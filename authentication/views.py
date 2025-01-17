from django.contrib.auth import views as auth_views
import simplejson as json
from django.http import HttpResponse, Http404
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
from django.shortcuts import render, redirect, get_object_or_404
from .forms import ResetPasswordForm, SignUpForm, LoginForm, ChangePasswordForm, LegalInformationForm, CorporationInviteForm, CorporationSignUpForm, AccountActivationForm
from .tokens import account_activation_token, affiliate_token_generator
from django.utils.encoding import force_text, force_bytes
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.timezone import timedelta, now
from messaging import email
from django.contrib.auth.tokens import default_token_generator
from .models import Affiliate
from django.contrib.auth.mixins import LoginRequiredMixin
from payments.models import Subscription, Corporation
from django.utils.translation import gettext as _


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
                    messages.error(request, _("Your account has been deactivated."))
                    return render(request, 'authentication/login.html', {'form': LoginForm()})
            else:
                messages.error(request, _("Failed to log in!"))
                return redirect("login")
        else:
            print(form.errors)
            messages.error(request, _("Failed to log in!"))
            return render(request, 'authentication/login.html', {'form': LoginForm(), 'form_errors': form.errors})
    else:
        return render(request, 'authentication/login.html', {'form': LoginForm()})


def user_signup(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    default_form = None
    corporation_form = None
    form = None

    if request.method == 'POST':
        if 'company_name' in request.POST:
            form = CorporationSignUpForm(request.POST)
            corporation_form = form
        else:
            form = SignUpForm(request.POST)
            default_form = form

        if form.is_valid():
            form.save_and_notify(request)
            return render(request, 'authentication/check_email.html', {})
        else:
            if form.has_error('email', 'unique'):
                del form._errors['email']

            if form.is_valid():
                # someone is attempting to register twice with same email
                # or checking if account with email exists
                user_email = request.POST['email'].strip()
                user = get_user_model().objects.get(email=user_email)
                email.send_to_single(user_email, 'register_with_known_email',
                                     request,
                                     first_name=user.first_name,
                                     last_name=user.last_name,
                                     token=default_token_generator.make_token(user),
                                     uid=urlsafe_base64_encode(force_bytes(user.pk))
                                     )
                return render(request, 'authentication/check_email.html', {})


    country = request.geolocation['county']['code'] if hasattr(request, 'geolocation') else ''
    context = {"form": SignUpForm(initial={'company_country':country}) if default_form is None else default_form,
                "open_form": form,
                "corporation_form": CorporationSignUpForm(initial={'company_country':country}) if corporation_form is None else corporation_form}
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
    success_url = reverse_lazy('account_legal_info', kwargs={'category':'legal_info'})
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
        messages.success(self.request, _('Password changed'))
        return super().form_valid(form)


@sensitive_post_parameters()
@csrf_protect
def activate_account(request, uidb64, token):
    u_model = get_user_model()
    form = None
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = u_model.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, u_model.DoesNotExist):
        user = None

    if user is not None and account_activation_token.check_token(user, token):
        if request.method == 'POST':
            form = AccountActivationForm(request.POST, user=user)
            if form.is_valid():
                user.activate_account()
                affiliates = Affiliate.objects.filter(receiver=user)
                if len(affiliates) > 0:
                    affiliates[0].confirm(request)
                login(request, user)
                messages.success(request, _('Your email address was confirmed and account activated.'))
                return redirect('dashboard')

        else:
            form = AccountActivationForm(user=user)


    return render(request, 'authentication/account_activation.html', dict(form=form))


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
                form.add_error('email', _('User already invited or registered'))

        form.clean = clean

        form.fields['message'].widget.attrs['rows'] = 5
        form.fields['email'].label = _("Friend's email")
        form.fields['name'].label = _("Friend's name")
        form.fields['message'].label = _("Message")

        form.helper = FormHelper()
        form.helper.add_input(Submit('submit', _('Send'), css_class='btn btn-primary'))
        form.helper.method = 'POST'
        form.helper.layout = Layout(Div(Div(Div('email', 'name', css_class='col'),
                                            Div('message', css_class='col'),
                                            css_class='row'),
                                        css_class=''))
        return form

    def form_valid(self, form):
        affiliate = form.save(commit=False)
        affiliate.sender = self.request.user

        affiliate.save()
        email.send_to_single(affiliate.email, 'affiliate_invitation', self.request,
                            affiliate=affiliate,
                            uid=urlsafe_base64_encode(force_bytes(affiliate.pk)),
                            token=affiliate_token_generator.make_token(affiliate))

        messages.success(self.request, _('Invitation sent to {0.name} ({0.email})').format(affiliate))
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

        default_form = None
        corporation_form = None
        form = None

        corporate_affiliate = False
        if affiliate.sender is not None:
            corporate_affiliate = affiliate.sender.member_of_corporation is not None

        if request.method == 'POST':
            if not corporate_affiliate and 'company_name' in request.POST:
                form = CorporationSignUpForm(request.POST)
                corporation_form = form
            else:
                form = SignUpForm(request.POST)
                default_form = form

            if form.is_valid():
                if form.cleaned_data['email'] == affiliate.email:
                    new_user = form.save(commit=False)
                    new_user.activate_account()
                    affiliate.receiver = new_user
                    affiliate.confirm(request)
                    login(request, new_user)
                    if new_user.member_of_corporation is None and new_user.company_name != '':
                        return redirect(reverse('plans') + '#corporate')
                    return redirect('dashboard')

                else:
                    new_user = form.save_and_notify(request)
                    affiliate.receiver = new_user
                    affiliate.save()
                    return render(request, 'authentication/check_email.html', {})

        country = request.geolocation['county']['code'] if hasattr(request, 'geolocation') else ''
        if default_form is None:
            default_form = SignUpForm(initial=dict(email=affiliate.email, first_name=affiliate.name, company_country=country))
        if corporation_form is None and not corporate_affiliate:
            corporation_form = CorporationSignUpForm(initial=dict(email=affiliate.email, first_name=affiliate.name, company_country=country))

        context = {"form": default_form,
                   "open_form": form,
                   "corporation_form": corporation_form}
        return render(request, 'authentication/signup.html', context)

    directions = _('You can use default <a href="{signup}">sign up form</a> or <a href="{login}">log in </a> to your account.'
                ).format(signup=reverse('signup'), login=reverse('login'))

    return render(request,
                  'authentication/invalid_affiliate_url.html',
                  {'directions':mark_safe(directions)})


@login_required
def legal_information_view(request, category=None):
    if request.method == 'POST':
        category = 'legal_info'
        form = LegalInformationForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save(commit=True)
            messages.success(request, _('Account changed successfully'))
        else:
            form_errors = (str(m.as_text()).lstrip('* ') for m in dict(form.errors).values())
            message = "<br>".join(form_errors)
            messages.error(request, mark_safe(message))

    else:
        form = LegalInformationForm(instance=request.user)
    subscription = None
    try:
        subscription = Subscription.objects.get(user=request.user,
                                                state__in=(Subscription.ACTIVE, Subscription.FAILURE_NOTIFIED))
    except Subscription.DoesNotExist:
        pass

    return render(request,
                  'authentication/legal_info.html',
                  dict(legal_info=form,
                       corporate_invitation=CorporationInviteForm(),
                       category=category,
                       subscription=subscription))


def _change_corporation_user(allow_self=False):
    def wrapper(make_changes):
        @login_required
        def wrapped(request):
            if request.method == 'POST' and request.user.manager_of_corporation is not None or (allow_self and request.user.member_of_corporation is not None):
                corporation = request.user.member_of_corporation
                target_user = get_object_or_404(get_user_model(),
                                            member_of_corporation=corporation,
                                            pk=request.POST.get('uid', ''))

                if target_user != corporation.owner:
                    make_changes(target_user, corporation)
                    target_user.save()
                    return redirect(reverse('account_legal_info', kwargs=dict(category='corporation')) + '#corporation')

            raise Http404()

        return wrapped
    return wrapper


@_change_corporation_user()
def assign_manager_role(user, corporation):
    user.manager_of_corporation = corporation


@_change_corporation_user()
def resign_manager_role(user, corporation):
    user.manager_of_corporation = None


@_change_corporation_user(True)
def remove_from_corporation(user, corporation):
    user.member_of_corporation = None
    user.manager_of_corporation = None


@login_required
def cancel_corporation_invitation(request):
    if request.method == 'POST' and request.user.manager_of_corporation is not None:
        corporation = request.user.manager_of_corporation
        try:
            target_user = get_user_model().objects.get(email=request.POST.get('email'))
        except get_user_model().DoesNotExist:
            try:
                affiliate = corporation.affiliate_set.get(email=request.POST.get('email'))
            except Affiliate.DoesNotExist:
                pass
            else:
                affiliate.requester = None
                affiliate.corporation = None
                affiliate.save()
        else:
            corporation.remove_invitation(user)
        return redirect(reverse(request.POST.get('next', 'account_legal_info')))

    raise Http404()


@login_required
def delete_or_leave_corporation(request):
    corp = request.user.member_of_corporation
    if corp is not None:
        user = request.user
        if user == corp.owner:
            corp.delete()
        else:
            user.member_of_corporation = None
            user.manager_of_corporation = None
            user.save()
    return redirect(reverse('account_legal_info'))


@login_required
def invite_into_corporation(request):
    if request.method == 'POST' and request.user.manager_of_corporation is not None:
        corporation = request.user.manager_of_corporation
        if not corporation.allow_invites:
            raise Http404()

        form = CorporationInviteForm(request.POST)
        invitation_sent = False
        if form.is_valid():
            try:
                recipient = get_user_model().objects.get(email=form.cleaned_data['email'])
            except get_user_model().DoesNotExist:
                try:
                    Affiliate.objects.get(email=form.cleaned_data['email'])
                except Affiliate.DoesNotExist:
                    affiliate = Affiliate.objects.create(email=form.cleaned_data['email'],
                                                        name=form.cleaned_data['name'],
                                                        sender=request.user,
                                                        corporation=corporation)
                    email.send_to_single(affiliate.email, 'affiliate_invitation', request,
                                        affiliate=affiliate,
                                        uid=urlsafe_base64_encode(force_bytes(affiliate.pk)),
                                        token=affiliate_token_generator.make_token(affiliate))

                    invitation_sent = True

            else:
                if recipient.member_of_corporation is None:
                    corporation.invite_user(recipient)
                    invitation_sent = True

        if not invitation_sent:
            messages.error(request,
                            _('{email} already invited or joined another corporation').format(email=form.cleaned_data['email']))

        return redirect(reverse('account_legal_info', kwargs=dict(category='corporation')) + '#corporation')

    raise Http404()


@login_required
def accept_corporation_invitation(request, corp_id):
    user = request.user
    if user.member_of_corporation is None:
        corporation = get_object_or_404(Corporation,
                                        pk=corp_id,
                                        _invited_users__contains= ' ' + user.email + ' ')

        user.member_of_corporation = corporation

        for corp in Corporation.objects.filter(_invited_users__contains= ' ' + user.email + ' '):
            corp.remove_invitation(user)
        user.save()
        messages.success(request, _('You are now member of {team} team').format(team=corporation.name))
        return redirect(reverse('dashboard'))

    raise Http404()


@login_required
def decline_corporation_invitation(request, corp_id):
    try:
        Corporation.objects.get(pk=corp_id).remove_invitation(request.user)
    except Corporation.DoesNotExist:
        pass

    return redirect(reverse('dashboard'))

