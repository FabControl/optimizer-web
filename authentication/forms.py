from django import forms
from .models import User
from django.contrib.auth.forms import UserCreationForm
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Row, Column, Field
from django.forms import ModelForm


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

    helper = FormHelper()
    helper.form_tag = False

    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'password1', 'password2',)

