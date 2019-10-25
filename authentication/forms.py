from django import forms
from .models import User
from django.contrib.auth.forms import UserCreationForm, PasswordResetForm
from crispy_forms.helper import FormHelper
from django.utils import safestring
from crispy_forms.layout import Submit, Layout, Row, Column, Field
from django.forms import ModelForm
from messaging import email
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode


# class UserForm(forms.ModelForm):
#     password = forms.CharField(widget=forms.PasswordInput())
#
#     class Meta:
#         model = User
#         fields = ('username', 'password', 'email')


class SignUpForm(UserCreationForm):
    username = None
    email = forms.EmailField(max_length=254, help_text='We will not share your email address with 3rd parties.')
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    company = forms.CharField(max_length=30, required=False)
    termsofuse = forms.BooleanField()
    termsofuse.label = safestring.mark_safe(
        '<label class="small">I agree to <a href="/help/terms_of_use" target="blank">terms of use</a></label>')

    helper = FormHelper()
    helper.form_tag = False

    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'password1', 'password2',)

    def save_and_notify(self, request):
        result = self.save()
        email.send_to_single(self.cleaned_data.get('email'), 'register_complete',
                             request,
                             receiving_user=' '.join((self.cleaned_data.get('first_name'),
                                                      self.cleaned_data.get('last_name')))
                             )
        return result


class ResetPasswordForm(PasswordResetForm):
    def __init__(self, *a, **k):
        super(ResetPasswordForm, self).__init__(*a, **k)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.fields["email"].help_text = "Password recovery instructions will be sent to this email."

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
