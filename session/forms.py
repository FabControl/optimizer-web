import logging
from django import forms
from django.urls import reverse_lazy
from django.utils.safestring import mark_safe
from crispy_forms.layout import Submit, Layout, Row, Column, Field, HTML
from crispy_forms.helper import FormHelper
from .models import *
from .choices import TEST_NUMBER_CHOICES


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
    def __init__(self, tested_values, units, attrs=None):
        # tested_values[0] is column, tested_values[1] is row

        super(TestValidationWidget, self).__init__(attrs)
        self.tested_values = tested_values
        if tested_values[1] is not None:
            self.bundled_values = [[(x, _) for x, _ in enumerate(tested_values[0])],
                                   [(y, _) for y, _ in enumerate(tested_values[1])]]
        else:
            self.bundled_values = [[(x, _) for x, _ in enumerate(tested_values[0])], []]

        self.units = tuple(map(self._to_printable_units, units))

        self.template_name = "session/widgets/test_validation_widget.html"

    def _to_printable_units(self, unit):
        if unit == '-': return ''
        if unit == 'degC': return '°C'
        return unit

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context["tested_values"] = self.tested_values
        context["bundled_values"] = self.bundled_values
        context["units"] = self.units
        return context

    def decompress(self, value):
        if value:
            return str(value)
        else:
            return ['', '']


class TestValidationField(forms.Field):
    def __init__(self, tested_values, units, *args, **kwargs):
        super(TestValidationField, self).__init__(*args, **kwargs)
        self.widget = TestValidationWidget(tested_values, units)
        self.tested_values = tested_values

    def to_python(self, value):
        try:
            indices = [int(x) for x in value.strip("[]").split(",")]
            return [self.tested_values[0][indices[0]], self.tested_values[1][indices[1]]]
        except ValueError:
            indices = [int(x) for x in value.strip("[]").split(",")[0]]
            return [self.tested_values[0][indices[0]], None]


class RangeSliderWidget(forms.widgets.Input):
    def __init__(self, value_range, units, attrs=None):
        # tested_values[0] is column, tested_values[1] is row
        super(RangeSliderWidget, self).__init__(attrs)
        self.value_range = value_range
        self.units = units
        self.template_name = "session/widgets/range_slider_widget.html"

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context["range"] = self.value_range
        context["units"] = self.units
        return context

    def decompress(self, value):
        if value:
            return value
        else:
            return None


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
        self.user = kwargs.pop("user", None)
        super(SessionForm, self).__init__(*args, **kwargs)
        self.fields["material"] = forms.ModelChoiceField(queryset=Material.objects.filter(owner=self.user))
        self.fields["machine"] = forms.ModelChoiceField(queryset=Machine.objects.filter(owner=self.user))

        self.fields["name"].label = "Session name"
        self.fields["material"].label = 'Material'
        self.fields["material"].help_text = mark_safe('<a href="{}?next={}">+ New Material</a>'.format(reverse_lazy('material_form'), reverse_lazy('new_session')))
        self.fields["machine"].label = "Machine"
        self.fields["machine"].help_text = mark_safe('<a href="{}?next={}">+ New Machine</a>'.format(reverse_lazy('machine_form'), reverse_lazy('new_session')))
        self.fields["target"].label = "Optimization Strategy"

        self.helper = FormHelper()
        self.helper.form_tag = False


class SettingForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(SettingForm, self).__init__(*args, **kwargs)

        self.fields['track_height_raft'].label = "First layer track height (mm)"
        self.fields['track_height_raft'].field_class = "field-horizontal"

        self.fields['speed_printing_raft'].label = 'First layer printing speed (mm/s)'
        self.fields['temperature_extruder_raft'].label = 'First layer extrusion temperature (°C)'
        self.fields['temperature_printbed_setpoint'].label = 'Print bed temperature (°C)'
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

        self.fields["validation"] = TestValidationField(session.tested_values, session.tested_value_units, required=True)
        self.fields["validation"].label = ""

        if len(session.min_max_parameters) == 3:
            parameter = session.min_max_parameters[-1]
            param = None
            if parameter["units"] != 'mm' and parameter["programmatic_name"] != "extrusion_multiplier":
                param = forms.IntegerField(min_value=parameter["values"][0], max_value=parameter["values"][1], widget=RangeSliderWidget([parameter["values"][0], parameter["values"][1]], parameter["units"]))
            elif parameter["programmatic_name"] == "extrusion_multiplier":
                param = forms.DecimalField(min_value=parameter["values"][0], max_value=parameter["values"][1], widget=RangeSliderWidget([parameter["values"][0], parameter["values"][1]], parameter["units"]))
            param.label = "{}".format(parameter["name"].capitalize())
            param.help_text = "Please select the best {} along the width of the selected substructure ({} {} - {} {}):".format(parameter["name"], str(parameter["values"][0]), parameter["units"], str(parameter["values"][-1]), parameter["units"])
            self.fields["min_max_parameter_three"] = param

        self.fields["comments"] = forms.CharField(max_length=256,
                                                  required=False, label='Comment')

        self.helper = FormHelper()
        self.helper.form_tag = False

    def save(self, commit=True):
        self.instance.selected_parameter_value("selected_parameter_one_value", self.cleaned_data["validation"][0])
        self.instance.selected_parameter_value("selected_parameter_two_value", self.cleaned_data["validation"][1])
        if "min_max_parameter_three" in self.cleaned_data:
            self.instance.selected_parameter_value("selected_parameter_three_value", self.cleaned_data["min_max_parameter_three"])
        if "comments" in self.cleaned_data:
            self.instance.alter_previous_tests(-1, 'comments', self.cleaned_data["comments"] or 0)
        return super(TestValidateForm, self).save(commit=commit)

    class Meta:
        model = Session
        fields = []


class TestGenerateForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(TestGenerateForm, self).__init__(*args, **kwargs)
        session = self.instance
        test_info = session.update_test_info()
        self.parameters = []
        secondary_parameters = []
        self.secondary_parameters_programmatic_names = []

        # Get all non-None parameters
        for item in test_info.items():
            if item[0].startswith("parameter"):
                if item[1] is not None:
                    if item[1]["name"] is not None:
                        self.parameters.append(('min_max_{}'.format(item[0]), item[1]))

        # Containers for active and inactive (readonly) fields
        actives = {}
        inactives = {}

        # Creating custom form fields for min_max
        for parameter in session.min_max_parameters:
            if parameter["active"]:
                if parameter["name"] is not None:
                    field_id = "min_max_{}".format(parameter["parameter"])
                    widgets = []
                    highest_iterable = parameter["iterable_values"][-1][0]
                    for iterable, value in parameter["iterable_values"]:
                        subwidget = forms.NumberInput(attrs={
                                "class": "form-control",
                                "type": ("text" if iterable not in [0, highest_iterable] else "number"),
                                "id": "linspace-field-{}".format(str(iterable)),
                                "value": round(value, (3 if parameter["units"] in ["mm", "-"] else 0)),
                                "step": ("0.001" if parameter["units"] in ["mm", "-"] else "1"),
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

                    self.fields[field_id].label = "{} ({})".format(parameter["name"].capitalize(), (
                        "°C" if parameter["units"] == "degC" else parameter["units"]))

                    if parameter['hint_active']:
                        self.fields[field_id].help_text = "{}".format(parameter['hint_active'])

        for secondary_parameter in test_info["other_parameters"]:
            secondary_parameters.append(secondary_parameter)

        # Create fields for secondary_parameters
        for parameter in secondary_parameters:
            if parameter["units"] != 'mm' and parameter["programmatic_name"] != "extrusion_multiplier":
                param = forms.IntegerField(min_value=parameter["min_max"][0], max_value=parameter["min_max"][1])
            elif parameter["programmatic_name"] == "extrusion_multiplier":
                param = forms.DecimalField(min_value=parameter["min_max"][0], max_value=parameter["min_max"][1])
            else:
                param = forms.DecimalField(min_value=parameter["min_max"][0], max_value=parameter["min_max"][1])
            param.label = "{} ({})".format(parameter["name"].capitalize(), (
                    "°C" if parameter["units"] == "degC" else parameter["units"]))
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
                if parameter["hint_active"]:
                    param.help_text = "{}".format(parameter["hint_active"])
            self.secondary_parameters_programmatic_names.append(parameter["programmatic_name"])

        #  Instantiate active fields first, so that they would appear on top
        for name, field in actives.items():
            self.fields[name] = field

        for name, field in inactives.items():
            self.fields[name] = field

        previously_tested = self.secondary_parameters_programmatic_names + [parameter["programmatic_name"] for parameter in session.min_max_parameters]
        if session.test_number == "01" or session.test_number == "02":
            if "part_cooling_setpoint" in previously_tested:
                previously_tested.remove("part_cooling_setpoint")

        if self.is_valid():
            session.previously_tested_parameters = previously_tested

        # Disable form tags
        self.helper = FormHelper()
        self.helper.form_tag = False

    def save(self, commit: bool = True):
        settings = self.instance.__getattribute__("settings")
        for parameter, info in self.parameters:
            if info["active"]:
                logging.getLogger("views").info("Currently saving {}: {}".format(parameter, self.cleaned_data[parameter]))
                self.instance.__setattr__(parameter, self.cleaned_data[parameter])
            else:
                self.instance.__setattr__(parameter, [self.cleaned_data[info["programmatic_name"]]])
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
        self.fields["buildarea_maxdim1"].label = "Maximum dimension on X axis (mm)"
        self.fields["buildarea_maxdim2"].label = "Maximum dimension on Y axis (mm)"

        self.fields["offset_1"].label = "Offset on X axis (mm)"
        self.fields["offset_2"].label = "Offset on Y axis (mm)"

        self.fields["form"].label = "Build area form factor"

        self.fields["gcode_header"].label = "Header"
        self.fields["gcode_header"].required = False
        self.fields["gcode_footer"].label = "Footer"
        self.fields["gcode_footer"].required = False

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
            ),
            Row(
                Column("extruder_type", css_class='form-group col-md')
            ),
        )

    class Meta:
        model = Machine
        fields = ["model",
                  "buildarea_maxdim1",
                  "buildarea_maxdim2",
                  "form",
                  "extruder_type",
                  "gcode_header",
                  "gcode_footer",
                  "offset_1",
                  "offset_2"]


class NewExtruderForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(NewExtruderForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False

        self.fields["tool"].label = "Gcode tool index"
        self.fields["temperature_max"].label = "Maximum temperature (°C)"

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
