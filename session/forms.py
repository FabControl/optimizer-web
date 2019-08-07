from django import forms
from .choices import TEST_NUMBER_CHOICES
from .models import Session, Material, Machine, Settings
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout


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
        fields = ('name', 'material', 'machine', 'slicer', 'target')

    def __init__(self, *args, **kwargs):
        # first call parent's constructor
        super(SessionForm, self).__init__(*args, **kwargs)
        # there's a `fields` property now
        self.fields['slicer'].required = False


class SettingForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(SettingForm, self).__init__(*args, **kwargs)
        self.fields['min_max_parameter_one_min'].label = 'First layer track height (mm)'
        self.fields['min_max_parameter_one_max'].label = ''
        self.fields['min_max_parameter_two_min'].label = 'First layer printing speed (mm/s)'
        self.fields['min_max_parameter_two_max'].label = ''
        self.fields['track_height_raft'].label = "First layer track height (mm)"
        self.fields['speed_printing_raft'].label = 'First layer printing spped (mm/s)'
        self.fields['temperature_extruder_raft'].label = 'First layer extrusion temperature (degC)'
        self.fields['temperature_printbed_setpoint'].label = 'Pritbed temperature (degC)'
        self.fields['track_width_raft'].label = 'First layer track width (mm)'

        self.helper = FormHelper()
        self.helper.field_class = 'col-lg-3'
        #
        # self.helper.add_input(Submit('submit', 'Submit'))
        # self.helper.layout = Layout(
        #     'email',
        #     'password',
        #     'remember_me',
        #     StrictButton('Sign in', css_class='btn-default'),
        # )

    class Meta:
        model = Settings
        fields = ('min_max_parameter_one_min',
                  'min_max_parameter_one_max',
                  'min_max_parameter_two_min',
                  'min_max_parameter_two_max',
                  'track_height_raft',
                  'speed_printing_raft',
                  'temperature_extruder_raft',
                  'temperature_printbed_setpoint',
                  'track_width_raft')

# Target: str from drop-down menu (m, f, a)
# First layer track height (mm): float from min to max or default
# First layer printing speed (mm/s): float from min to max
# First layer extrusion temperature (°C): float
# Print bed temperature (°C): float
# First layer track width (mm): float
