from django import forms
from .choices import TEST_NUMBER_CHOICES
from .models import Session, Material, Machine, Settings
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Row, Column
from django.template import loader
from django.utils.safestring import mark_safe
import logging
from optimizer_api import api_client
import json


class MinMaxWidget(forms.widgets.MultiWidget):
    def __init__(self, widgets: list, attrs=None):
        widgets = widgets
        super(MinMaxWidget, self).__init__(widgets, attrs)
        self.template_name = "session/widgets/min_max_widget.html"

    def decompress(self, value):
        if value:
            if len(value) > 1:
                return [float(value[0]), float(value[-1])]
            else:
                return [float(value[0])]
        else:
            return ['', '']


class MinMaxField(forms.MultiValueField):
    def __init__(self, fields, *args, **kwargs):
        list_fields = fields
        super(MinMaxField, self).__init__(list_fields, *args, **kwargs)

    def compress(self, data_list):
        if len(data_list) > 1:
            return [float(data_list[0]), float(data_list[-1])]
        elif len(data_list) == 1:
            return [float(data_list[0])]
        else:
            return []


class NewTestForm(forms.Form):
    session_name = forms.CharField(label='Session name', max_length=20,
                                   error_messages={'required': 'Please enter session name'})
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

        self.fields['track_height_raft'].label = "First layer track height (mm)"
        self.fields['track_height_raft'].field_class = "field-horizontal"

        self.fields['speed_printing_raft'].label = 'First layer printing spped (mm/s)'
        self.fields['temperature_extruder_raft'].label = 'First layer extrusion temperature (°C)'
        self.fields['temperature_printbed_setpoint'].label = 'Pritbed temperature (°C)'
        self.fields['track_width_raft'].label = 'First layer track width (mm)'

        self.helper = FormHelper()
        # self.helper.form_class = 'form-horizontal'
        # self.helper.field_class = 'col-lg-3'
        # self.helper.label_class = 'col-lg-6'
        self.helper.form_tag = False

        # self.helper.layout = Layout(
        #     # Row(
        #     #     Column('email', css_class='form-group col-md-6 mb-0'),
        #     #     Column('password', css_class='form-group col-md-6 mb-0'),
        #     #     css_class='form-row'
        #     # ),
        #     # Row(
        #     #     Column('min_max_parameter_one_min', css_class='form-group col-md-6 mb-0'),
        #     #     Column('min_max_parameter_one_max', css_class='form-group col-md-6 mb-0'),
        #     #     css_class='form-row'
        #     # ),
        #     # Row(
        #     #     Column('min_max_parameter_two_min', css_class='form-group col-md-6 mb-0'),
        #     #     Column('min_max_parameter_two_max', css_class='form-group col-md-6 mb-0'),
        #     #     css_class='form-row'
        #     # ),
        #     Row(
        #         Column('track_height_raft',
        #                'speed_printing_raft',
        #                'temperature_extruder_raft',
        #                'temperature_printbed_setpoint',
        #                'track_width_raft',
        #                css_class='form-group col-md-12 mb-0'),
        #     )
        # )

    class Meta:
        model = Settings
        fields = ('track_height_raft',
                  'speed_printing_raft',
                  'temperature_extruder_raft',
                  'temperature_printbed_setpoint',
                  'track_width_raft')


class TestValidateForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(TestValidateForm, self).__init__(*args, **kwargs)

        session = self.instance
        # previous_test = session.previous_tests[-1]["test_name"]

        self.fields["selected_value_one"] = forms.DecimalField()
        self.fields["selected_value_two"] = forms.DecimalField()

        self.fields["selected_value_one"].label = str(session.test_info["parameter_one"]["name"])
        self.fields["selected_value_two"].label = str(session.test_info["parameter_two"]["name"])

        self.helper = FormHelper()
        self.helper.form_tag = False

    def save(self, commit=True):
        self.instance.__getattribute__("previous_tests")[-1]["selected_parameter_one_value"] = self.cleaned_data[
            "selected_value_one"]
        self.instance.__getattribute__("previous_tests")[-1]["selected_parameter_two_value"] = self.cleaned_data[
            "selected_value_two"]
        return super(TestValidateForm, self).save(commit=commit)

    class Meta:
        model = Session
        fields = []


class TestGenerateForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(TestGenerateForm, self).__init__(*args, **kwargs)
        session = self.instance
        test_info = session.test_info
        self.parameters = []
        secondary_parameters = []
        self.secondary_parameters_programmatic_names = []

        # Get all non-None parameters
        for item in test_info.items():
            if item[0].startswith("parameter"):
                if item[1] is not None:
                    self.parameters.append(('min_max_{}'.format(item[0]), item[1]))

        # Creating custom form fields for min_max
        for parameter in session.min_max_parameters:
            if parameter["name"] is not None:
                field_id = "min_max_{}".format(parameter["parameter"])
                widgets = []
                highest_iterable = parameter["iterable_values"][-1][0]
                for iterable, value in parameter["iterable_values"]:
                    subwidget = forms.NumberInput(attrs={
                            "class": "form-control",
                            "name": "somename",
                            "type": ("text" if iterable not in [0, highest_iterable] else "number"),
                            "id": "linspace-field-{}".format(str(iterable)),
                            "value": round(value, (2 if parameter["units"] == "mm" else 0)),
                            "step": ("0.01" if parameter["units"] == "mm" else "1"),
                            "onchange": "change_fields(this)",
                        })
                    if iterable not in [0, highest_iterable]:
                        subwidget.attrs["type"] = "text"
                        subwidget.attrs["readonly"] = "readonly"
                    else:
                        subwidget.attrs["type"] = "number"
                    widgets.append(subwidget)

                self.fields[field_id] = MinMaxField(
                    fields=([forms.DecimalField(initial=x) for x in parameter["values"]]),
                    widget=MinMaxWidget(
                        widgets=widgets))

                self.fields[field_id].label = "{} ({})".format(parameter["name"].capitalize(), parameter["units"])

        for secondary_parameter in test_info["other_parameters"]:
            secondary_parameters.append(secondary_parameter)

        # Create fields for secondary_parameters
        for parameter in secondary_parameters:
            if parameter["units"] != 'mm':
                self.fields[parameter["programmatic_name"]] = forms.IntegerField()
            else:
                self.fields[parameter["programmatic_name"]] = forms.DecimalField()
            self.fields[parameter["programmatic_name"]].label = "{} ({})".format(parameter["name"].capitalize(),
                                                                                 parameter["units"])
            self.secondary_parameters_programmatic_names.append(parameter["programmatic_name"])

        # Layout primary and secondary_parameters
        self.helper = FormHelper()
        # self.helper.form_class = 'form-horizontal'
        # self.helper.field_class = 'col-lg-3'
        # self.helper.label_class = 'col-lg-6'
        self.helper.form_tag = False

        # Create Row and Column for each min_max parameter
        min_max_rows = []
        for parameter in self.parameters:
            col = Column(parameter, css_class='form-group col-md-6 mb-0')
            row = Row(col)
            min_max_rows.append(row)

        secondary_parameter_row = Row(
            Column(css_class='form-group col-md-6 mb-0', *self.secondary_parameters_programmatic_names))

        # self.helper.layout = Layout(*min_max_rows, secondary_parameter_row)

    def save(self, commit: bool = True):
        settings = self.instance.__getattribute__("settings")
        for parameter, info in self.parameters:
            # import pdb;
            # pdb.set_trace()
            logging.getLogger("views").info("Currently saving {}: {}".format(parameter, self.cleaned_data[parameter]))
            self.instance.__setattr__(parameter, self.cleaned_data[parameter])
        for setting in self.secondary_parameters_programmatic_names:
            logging.getLogger("views").info("Currently saving {}: {}".format(setting, self.cleaned_data[setting]))
            # import pdb;
            # pdb.set_trace()
            settings.__setattr__(setting, self.cleaned_data[setting])
        settings.save()

        return super(TestGenerateForm, self).save(commit=commit)

    class Meta:
        model = Session
        fields = []
