from django import forms
from .choices import TEST_NUMBER_CHOICES
from .models import Session, Material, Machine


class NewTestForm(forms.Form):
    session_name = forms.CharField(label='Session name', max_length=20, error_messages={'required': 'Please enter session name'})
    comments = forms.CharField(label='Comments', max_length=20, required=False, help_text='100 characters max.')
    test_number = forms.ChoiceField(choices=TEST_NUMBER_CHOICES)


class MachineForm(forms.ModelForm):
    class Meta:
        model = Machine
        fields = ('model', 'buildarea_maxdim1', 'buildarea_maxdim2')


class MaterialForm(forms.ModelForm):
    class Meta:
        model = Material
        fields = ('name', 'size_od')


class SessionForm(forms.ModelForm):
    class Meta:
        model = Session
        fields = ('name', 'material', 'machine', 'slicer')

    def __init__(self, *args, **kwargs):
        # first call parent's constructor
        super(SessionForm, self).__init__(*args, **kwargs)
        # there's a `fields` property now
        self.fields['slicer'].required = False

