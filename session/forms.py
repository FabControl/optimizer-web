from django import forms


class NewTestForm(forms.Form):
    your_name = forms.CharField(label='Session name', max_length=20)

