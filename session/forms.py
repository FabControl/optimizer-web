from django import forms
from .choices import TEST_NUMBER_CHOICES
from .models import *
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Row, Column, Field
import logging
from ast import literal_eval


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


class TestValidationWidget(forms.widgets.Input):
    def __init__(self, tested_values, attrs=None):
        # tested_values[0] is column, tested_values[1] is row

        super(TestValidationWidget, self).__init__(attrs)
        self.tested_values = tested_values
        if tested_values[1] is not None:
            self.bundled_values = [[(x, _) for x, _ in enumerate(tested_values[0])],
                                   [(y, _) for y, _ in enumerate(tested_values[1])]]
        else:
            self.bundled_values = [[(x, _) for x, _ in enumerate(tested_values[0])], []]

        self.template_name = "session/widgets/test_validation_widget.html"

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context["tested_values"] = self.tested_values
        context["bundled_values"] = self.bundled_values
        context["units"] = ["mm", "mm/s"]
        return context

    def decompress(self, value):
        if value:
            return str(value)
        else:
            return ['', '']


class TestValidationField(forms.Field):
    def __init__(self, tested_values, *args, **kwargs):
        super(TestValidationField, self).__init__(*args, **kwargs)
        self.widget = TestValidationWidget(tested_values=tested_values)
        self.tested_values = tested_values

    def to_python(self, value):
        try:
            indices = [int(x) for x in value.strip("[]").split(",")]
            return [self.tested_values[0][indices[0]], self.tested_values[1][indices[1]]]
        except ValueError:
            indices = [int(x) for x in value.strip("[]").split(",")[0]]
            return [self.tested_values[0][indices[0]], None]


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

    def __init__(self, *args, **kwargs):
        super(MaterialForm, self).__init__(*args, **kwargs)
        self.fields['name'].label = "Name"
        self.fields['size_od'].label = "Filament diameter (mm)"


class SessionForm(forms.ModelForm):
    class Meta:
        model = Session
        fields = ('name', 'material', 'machine', 'target')

    def __init__(self, *args, **kwargs):
        # first call parent's constructor
        super(SessionForm, self).__init__(*args, **kwargs)
        # there's a `fields` property now


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
        self.helper.form_tag = False

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

        self.fields["validation"] = TestValidationField(tested_values=session.tested_values)
        self.fields["validation"].label = "Select the best sub-structure:"

        self.helper = FormHelper()
        self.helper.form_tag = False

    def save(self, commit=True):
        self.instance.selected_parameter_value("selected_parameter_one_value", self.cleaned_data["validation"][0])
        self.instance.selected_parameter_value("selected_parameter_two_value", self.cleaned_data["validation"][1])
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
                    if item[1]["name"] is not None:
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
                            "min": round(parameter["min_max"][0], 3),
                            "max": round(parameter["min_max"][1], 3)
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

        # Containers for active and inactive (readonly) fields
        actives = {}
        inactives = {}

        # Create fields for secondary_parameters
        for parameter in secondary_parameters:
            if parameter["units"] != 'mm' and parameter["programmatic_name"] != "extrusion_multiplier":
                param = forms.IntegerField(min_value=parameter["min_max"][0], max_value=parameter["min_max"][1])
            elif parameter["programmatic_name"] == "extrusion_multiplier":
                param = forms.DecimalField(min_value=parameter["min_max"][0], max_value=parameter["min_max"][1])
            else:
                param = forms.DecimalField(min_value=parameter["min_max"][0], max_value=parameter["min_max"][1])
            param.label = "{} ({})".format(parameter["name"].capitalize(), parameter["units"])
            param.widget.attrs["class"] = "col-sm-2"
            param.initial = parameter["values"]
            if not parameter["active"]:
                param.widget.attrs['readonly'] = True
                inactives[parameter["programmatic_name"]] = param
            elif parameter["programmatic_name"] in session.get_previously_tested_parameters():
                param.widget.attrs['readonly'] = True
                inactives[parameter["programmatic_name"]] = param
            else:
                actives[parameter["programmatic_name"]] = param
            self.secondary_parameters_programmatic_names.append(parameter["programmatic_name"])

        #  Instantiate active fields first, so that they would appear on top
        for name, field in actives.items():
            self.fields[name] = field

        for name, field in inactives.items():
            self.fields[name] = field

        previously_tested = self.secondary_parameters_programmatic_names + [parameter["programmatic_name"] for parameter in session.min_max_parameters]
        if session.test_number == "01" or session.test_number == "02":
            previously_tested.remove("part_cooling_setpoint")
        session.previously_tested_parameters = previously_tested

        # Disable form tags
        self.helper = FormHelper()
        self.helper.form_tag = False

    def save(self, commit: bool = True):
        settings = self.instance.__getattribute__("settings")
        for parameter, info in self.parameters:
            logging.getLogger("views").info("Currently saving {}: {}".format(parameter, self.cleaned_data[parameter]))
            self.instance.__setattr__(parameter, self.cleaned_data[parameter])
        for setting in self.secondary_parameters_programmatic_names:
            logging.getLogger("views").info("Currently saving {}: {}".format(setting, self.cleaned_data[setting]))
            settings.__setattr__(setting, self.cleaned_data[setting])
        settings.save()

        return super(TestGenerateForm, self).save(commit=commit)

    class Meta:
        model = Session
        fields = []


class NewMachineForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(NewMachineForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False

        self.fields["model"].label = "Printer model"
        self.fields["buildarea_maxdim1"].label = "Build area maximum dimension on X axis (mm)"
        self.fields["buildarea_maxdim2"].label = "Build area maximum dimension on Y axis (mm)"
        self.fields["form"].label = "Build area form factor"

        self.helper.layout = Layout(
            Row(
                Column("model", css_class='form-group col-md'),
                css_class='form-row'
            ),
            Row(
                Column("buildarea_maxdim1", css_class='form-group col-md'),
                Column("buildarea_maxdim2", css_class='form-group col-md')
            ),
            Row(
                Column("form", css_class='form-group col-md')
            )
        )

    class Meta:
        model = Machine
        fields = ["model", "buildarea_maxdim1", "buildarea_maxdim2", "form"]


class NewExtruderForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(NewExtruderForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False

        self.fields["temperature_max_extruder"] = self.fields["temperature_max"]
        del self.fields["temperature_max"]

        self.fields["tool"].label = "Gcode tool index"
        self.fields["temperature_max_extruder"].label = "Maximum temperature (°C)"

    class Meta:
        model = Extruder
        fields = ["tool", "temperature_max", "part_cooling"]


class NewNozzleForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(NewNozzleForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False

        self.fields["size_id"].label = "Nozzle's inner diameter (mm)"

    class Meta:
        model = Nozzle
        fields = ["size_id"]


class NewChamberForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(NewChamberForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False

        self.fields["tool"].label = "Gcode tool index"
        self.fields["gcode_command"].label = "Gcode syntax"
        self.fields["temperature_max"].label = "Maximum temperature (°C)"
    class Meta:
        model = Chamber
        fields = ["chamber_heatable", "tool", "gcode_command", "temperature_max"]


class NewPrintbedForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(NewPrintbedForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False

        self.fields["temperature_max"].label = "Maximum temperature (°C)"
        self.fields["printbed_heatable"].label = "Print bed heatable"

    class Meta:
        model = Printbed
        fields = ["printbed_heatable", "temperature_max"]
