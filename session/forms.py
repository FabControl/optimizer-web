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
        fields = ('name', 'size_od', 'min_temperature', 'max_temperature', 'notes')

    def __init__(self, *args, **kwargs):
        super(MaterialForm, self).__init__(*args, **kwargs)

        self.fields['min_temperature'].label = "Min temperature (°C)"
        self.fields['min_temperature'].help_text = mark_safe("Manufacturer's suggested temperature. After the testing process you might end up with a different temperature. If you do not have this data, here is a method to determine it <a href='https://3doptimizer.helpscoutdocs.com/article/42-determining-initial-printing-temperature'>here</a>.")

        self.fields['max_temperature'].label = "Max temperature (°C)"
        self.fields['max_temperature'].help_text = "Same as above."

        self.fields['name'].label = "Name"
        self.fields['size_od'].label = "Filament diameter (mm)"
        self.fields['notes'].widget = forms.Textarea()
        self.fields['notes'].widget.attrs.update({'rows': '1'})
        self.fields['notes'].label = "Notes"
        self.fields['notes'].help_text = "(Batch number, color, SKU etc.)"
        self.fields['notes'].required = False


class SessionForm(forms.ModelForm):
    class Meta:
        model = Session
        fields = ('name', 'target', 'mode', 'machine', 'material')

    def __init__(self, *args, **kwargs):
        ownership = kwargs.pop("ownership", None)
        self.user = kwargs.pop("user", None)
        super(SessionForm, self).__init__(*args, **kwargs)
        self.fields["material"] = forms.ModelChoiceField(queryset=Material.objects.filter(ownership))
        self.fields["machine"] = forms.ModelChoiceField(queryset=Machine.objects.filter(ownership))

        modes = []
        initial = None
        for mode in SessionMode.objects.all():
            if self.user.plan in mode.plan_availability:
                modes.append(mode.pk)
                if mode.type == 'guided':
                    initial = mode

        queryset = SessionMode.objects.filter(pk__in=modes)

        self.fields["mode"] = forms.ModelChoiceField(initial=initial, queryset=queryset, widget=forms.RadioSelect, empty_label=None)
        self.fields["name"].label = "Name"
        self.fields["mode"].label = "Mode"
        self.fields["material"].label = 'Material'
        self.fields["material"].help_text = mark_safe('<a href="{}?next={}">+ New Material</a>'.format(reverse_lazy('material_form'), reverse_lazy('new_session')))
        self.fields["machine"].label = "3D Printer"
        self.fields["machine"].help_text = mark_safe('<a href="{}?next={}">+ New 3D Printer</a>'.format(reverse_lazy('machine_form'), reverse_lazy('new_session')))
        self.fields["target"].label = "Target"

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
                                                  required=False, label='My notes (optional)')

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


class ValidateFormTestDescriptionForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(ValidateFormTestDescriptionForm, self).__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_tag = False

        session = self.instance
        questions = Junction.objects.get(base_test=session.test_number).descriptors.all()
        for i, question in enumerate(questions):
            question_name = f'question_{str(i)}'
            choices = ((question.pk, "Yes"), ("null", "No"))
            q = forms.TypedChoiceField(choices=choices, initial="null", widget=forms.RadioSelect, required=True)
            if question.image:
                q.label = mark_safe(f"""<a type="button" href="#" class="" data-toggle="popover" data-trigger="focus" title=" " data-img='{question.image.url}'>{question.statement}</a>""")
            else:
                q.label = question.statement
            q.required = False
            q.widget.attrs.update({'value': question.pk})
            q.widget.attrs.update({'target': question.target_test})
            self.fields[question_name] = q

    class Meta:
        model = Session
        fields = []


class TestGenerateForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(TestGenerateForm, self).__init__(*args, **kwargs)
        show_inactives = True
        session = self.instance

        if session.mode.type == 'guided':
            show_inactives = False

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
                            subwidget.attrs["class"] = "form-control"
                        else:
                            subwidget.attrs["type"] = "number"
                            subwidget.attrs["class"] = "form-control optimizer-input"
                        widgets.append(subwidget)

                    self.fields[field_id] = MinMaxField(
                        fields=([forms.DecimalField(initial=x) for x in parameter["values"]]),
                        widget=MinMaxWidget(
                            widgets=widgets))

                    self.fields[field_id].label = "{} ({})".format(parameter["name"].capitalize(), (
                        "°C" if parameter["units"] == "degC" else parameter["units"]))

                    if parameter['hint_active']:
                        self.fields[field_id].help_text = "{}".format(parameter['hint_active'])

        list(self.fields.values())[-1].use_hr = True

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
            param.widget.attrs["class"] = "col-sm-2 optimizer-input"
            param.initial = parameter["values"]
            if not parameter["active"]:
                # TODO reintroduce functionality to show previously tested params
                if not show_inactives:
                    continue
                # param.widget.attrs['readonly'] = True
                # inactives[parameter["programmatic_name"]] = param
            elif parameter["programmatic_name"] in session.get_previously_tested_parameters():
                if not show_inactives:
                    continue
                # param.widget.attrs['readonly'] = True
                # inactives[parameter["programmatic_name"]] = param
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
        self.helper = FormHelper(self)
        self.helper.form_tag = False
        self.helper.field_template = 'session/field.html'

    def save(self, commit: bool = True):
        settings = self.instance.__getattribute__("settings")
        for parameter, info in self.parameters:
            if info["active"]:
                logging.getLogger("views").info("Currently saving {}: {}".format(parameter, self.cleaned_data[parameter]))
                self.instance.__setattr__(parameter, self.cleaned_data[parameter])
            else:
                if info["programmatic_name"] in self.cleaned_data:
                    self.instance.__setattr__(parameter, [self.cleaned_data[info["programmatic_name"]]])
        for setting in self.secondary_parameters_programmatic_names:
            if setting in self.cleaned_data:
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

        self.fields["model"].label = "3D Printer model"
        self.fields["buildarea_maxdim1"].label = "Max dimension on X axis (mm)"
        self.fields["buildarea_maxdim2"].label = "Max dimension on Y axis (mm)"

        self.fields["offset_1"].label = "Offset on X axis (mm)"
        self.fields["offset_2"].label = "Offset on Y axis (mm)"

        self.fields["form"].label = "Type"

        self.fields["gcode_header"].label = "Header"
        self.fields["gcode_header"].required = False
        self.fields["gcode_header"].widget.attrs.update({'rows': '4'})
        self.fields["gcode_footer"].label = "Footer"
        self.fields["gcode_footer"].required = False
        self.fields["gcode_footer"].widget.attrs.update({'rows': '4'})
        self.fields["homing_sequence"].required = True
        self.fields["homing_sequence"].label = "Homing script"
        self.fields["homing_sequence"].widget.attrs.update({'rows': '4'})
        self.helper.layout = Layout(
            Row(
                Column("model", css_class='form-group col-md'),
                css_class='form-row'
            ),
            Row(
                Column("form", css_class='form-group col-md')
            ),
            Row(
                Column("buildarea_maxdim1", css_class='form-group col-md'),
                Column("buildarea_maxdim2", css_class='form-group col-md')
            ),
            Row(
                Column("extruder_type", css_class='form-group col-md')
            ),
        )


    class Meta:
        model = Machine
        fields = ["model",
                  "form",
                  "buildarea_maxdim1",
                  "buildarea_maxdim2",
                  "extruder_type",
                  "gcode_header",
                  "gcode_footer",
                  "homing_sequence",
                  "offset_1",
                  "offset_2"]


class NewExtruderForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(NewExtruderForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False

        self.fields["tool"].label = "Gcode tool index"
        self.fields["temperature_max"].label = "Max temperature (°C)"

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
        self.fields["temperature_max"].label = "Max temperature (°C)"

    class Meta:
        model = Chamber
        fields = ["chamber_heatable", "tool", "gcode_command", "temperature_max"]


class NewPrintbedForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(NewPrintbedForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False

        self.fields["temperature_max"].label = "Max temperature (°C)"
        self.fields["printbed_heatable"].label = "Print bed heatable"

    class Meta:
        model = Printbed
        fields = ["printbed_heatable", "temperature_max"]
