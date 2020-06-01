from django import forms
from .models import User
from django.contrib.auth.forms import UserCreationForm, PasswordResetForm, PasswordChangeForm, SetPasswordForm
from crispy_forms.helper import FormHelper
from django.utils import safestring
from crispy_forms.layout import Submit, Layout, Row, Column, Field
from django.forms import ModelForm
from messaging import email
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth import get_user_model
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from payments.countries import codes_iso3166
from payments.models import Corporation


# class UserForm(forms.ModelForm):
#     password = forms.CharField(widget=forms.PasswordInput())
#
#     class Meta:
#         model = User
#         fields = ('username', 'password', 'email')


class LoginForm(forms.Form):

    email = forms.EmailField()
    password = forms.CharField(max_length=32, widget=forms.PasswordInput)

    def __init__(self, *args, **kwargs):
        super(LoginForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False

    class Meta:
        fields = ['email', 'password']


class SignUpForm(UserCreationForm):
    username = None
    email = forms.EmailField(max_length=254, help_text='We will not share your email address with 3rd parties.')
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    termsofuse = forms.BooleanField()
    termsofuse.label = safestring.mark_safe('<label class="small">I agree to <a href="/help/terms_of_use" target="blank">terms of use</a></label>')

    helper = FormHelper()
    helper.form_tag = False

    def __init__(self, *args, **kwargs):
        super(SignUpForm, self).__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs["maxlength"] = 32
        self.fields['password2'].widget.attrs["maxlength"] = 32
        self.fields['password1'].widget.attrs["minlength"] = 8
        self.fields['password2'].widget.attrs["minlength"] = 8
        self.fields['company_country'].label = 'Country'

    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'password1', 'password2', 'company_country')

    def save_and_notify(self, request):
        user = self.save()
        user.send_account_activation(request)
        return user


class CorporationSignUpForm(SignUpForm):
    company_name = forms.CharField(max_length=30, required=True)
    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'password1', 'password2', 'company_country', 'company_name')

    def save(self, *a, **k):
        user = super().save(*a, **k)
        if len(user.corporation_set.all()) < 1:
            corp_name = user.company_name if user.company_name != '' else f"{user.first_name}'s corporation"
            corp = Corporation.objects.create(owner=user,
                                        name=corp_name)
            user.member_of_corporation = corp
            user.manager_of_corporation = corp
            user.save()
        return user


class ResetPasswordForm(PasswordResetForm):
    def __init__(self, *a, **k):
        super(ResetPasswordForm, self).__init__(*a, **k)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.fields["email"].help_text = "Password recovery instructions will be sent to this email."

    def get_users(self, email):
        # Reimplemented to allow activate account with expired activation token
        usr_model = get_user_model()
        active_users = usr_model._default_manager.filter(**{
        '%s__iexact' % usr_model.get_email_field_name(): email,
        })
        return (u for u in active_users if u.has_usable_password())

    def save(self, domain_override=None,
             subject_template_name='registration/password_reset_subject.txt',
             email_template_name='registration/password_reset_email.html',
             use_https=False, token_generator=default_token_generator,
             from_email=None, request=None, html_email_template_name=None,
             extra_email_context=None):
        """
        Generate a one-use only link for resetting password and send it to the
        user.
        """
        user_email = self.cleaned_data["email"]
        email_valid = False
        for user in self.get_users(user_email):
            email.send_to_single(user_email, 'password_recovery',
                                 request,
                                 receiving_user=' '.join((user.first_name, user.last_name)),
                                 token=default_token_generator.make_token(user),
                                 uid=urlsafe_base64_encode(force_bytes(user.pk))
                                 )
            email_valid = True

        if not email_valid:
            email.send_to_single(user_email, 'password_recovery_failure',
                                 request,
                                 requested_email=user_email)


class ChangePasswordForm(PasswordChangeForm):
    def __init__(self, *a, **k):
        super(PasswordChangeForm, self).__init__(*a, **k)
        self.helper = FormHelper()
        self.helper.form_tag = False

class PasswordSetForm(SetPasswordForm):
    def save(self, commit=True):
        password = self.cleaned_data["new_password1"]
        self.user.set_password(password)
        self.user.is_active = True
        if commit:
            self.user.save()
        return self.user


class LegalInformationForm(forms.ModelForm):
    company_account = forms.BooleanField(required=False)
    class Meta:
        model = User
        fields = ('first_name', 'last_name',
                  'company_name', 'company_country',
                  'company_legal_address', 'company_registration_number',
                  'company_vat_number')

    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self.fields['company_name'].label = 'Company name*'
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True
        self.fields['company_country'].label = 'Country'
        self.fields['company_legal_address'].label = 'Company legal address*'
        self.fields['company_registration_number'].label = 'Company registration number*'
        self.fields['company_vat_number'].label = 'Company VAT number'
        self.fields['company_account'].initial = self.instance.is_company_account
        self.fields['company_account'].label = 'Show legal info (for EU companies)'

    def clean(self):
        cleaned_data = super().clean()
        company_account = cleaned_data.get('company_account')
        if not company_account:
            cleaned_data['company_vat_number'] = ''

        missing = []
        for f in ['company_name', 'company_country', 'company_legal_address', 'company_registration_number']:
            if company_account:
                v = cleaned_data.get(f)
                if v == '' or v is None:
                    missing.append(self.fields[f].label)

            elif f != 'company_country':
                cleaned_data[f] = ''

        if len(missing) > 0:
            if len(missing) > 1:
                last = missing.pop()
                msg = ', '.join(missing) + ' and ' + last
            else:
                msg = missing[0]

            raise forms.ValidationError(
                    'Company account requires: ' + msg + '.'
                    )

        return cleaned_data


class CorporationInviteForm(forms.Form):
    email = forms.EmailField(widget=forms.TextInput(attrs={'placeholder': 'email'}))
    name = forms.CharField(max_length=20, widget=forms.TextInput(attrs={'placeholder': 'name'}))

    class Meta:
        fields = ['email', 'name']
