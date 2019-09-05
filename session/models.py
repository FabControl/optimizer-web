from django.db import models
from datetime import datetime
from .choices import TEST_NUMBER_CHOICES, TARGET_CHOICES, SLICER_CHOICES, TOOL_CHOICES, FORM_CHOICES, UNITS
import ast
import simplejson as json
from optimizer_api import api_client


# Create your models here.


class Material(models.Model):
    size_od = models.DecimalField(default=1.75, max_digits=3, decimal_places=2)
    name = models.CharField(max_length=60)
    pub_date = models.DateTimeField(default=datetime.now, blank=True)

    def __str__(self):
        return "{} ({} mm)".format(self.name, str(self.size_od))

    @property
    def __json__(self):
        output = {
            "size_od": self.size_od,
            "name": self.name
        }
        return output


class Nozzle(models.Model):
    size_id = models.DecimalField(default=0.4, decimal_places=1, max_digits=2)

    @property
    def __json__(self):
        output = {
            "size_id": self.size_id
        }
        return output


class Extruder(models.Model):
    pub_date = models.DateTimeField(default=datetime.now, blank=True)

    tool = models.CharField(choices=TOOL_CHOICES, max_length=3, blank=True, default="T0")
    temperature_max = models.IntegerField(default=350)
    part_cooling = models.BooleanField(default=True)
    nozzle = models.ForeignKey(Nozzle, on_delete=models.CASCADE)

    @property
    def __json__(self):
        output = {
            "tool": self.tool,
            "temperature_max": self.temperature_max,
            "part_cooling": self.part_cooling,
            "nozzle": self.nozzle.__json__
        }
        return output


class Chamber(models.Model):
    chamber_heatable = models.BooleanField(default=False)
    tool = models.CharField(max_length=3, choices=TOOL_CHOICES, blank=True)
    gcode_command = models.CharField(max_length=40, default="M141 S$temp")
    temperature_max = models.IntegerField(default=80)

    @property
    def __json__(self):
        output = {
            "tool": self.tool,
            "gcode_command": self.gcode_command,
            "temperature_max": self.temperature_max,
            "chamber_heatable": self.chamber_heatable
        }
        return output


class Printbed(models.Model):
    printbed_heatable = models.BooleanField(default=True)
    temperature_max = models.IntegerField(default=120)

    @property
    def __json__(self):
        output = {
            "printbed_heatable": self.printbed_heatable
        }
        return output


class Machine(models.Model):
    pub_date = models.DateTimeField(default=datetime.now, blank=True)
    model = models.CharField(max_length=30, default="Unknown")
    buildarea_maxdim1 = models.IntegerField(default=0)
    buildarea_maxdim2 = models.IntegerField(default=0)
    form = models.CharField(max_length=20, choices=FORM_CHOICES, default="cartesian")
    extruder = models.ForeignKey(Extruder, on_delete=models.PROTECT)
    chamber = models.ForeignKey(Chamber, on_delete=models.CASCADE, blank=True)
    printbed = models.ForeignKey(Printbed, on_delete=models.CASCADE, blank=True)

    def __str__(self):
        return self.model

    @property
    def __json__(self):
        output = {
            "model": self.model,
            "buildarea_maxdim1": self.buildarea_maxdim1,
            "buildarea_maxdim2": self.buildarea_maxdim2,
            "form": self.form,
            "temperature_controllers": {
                "extruder": self.extruder.__json__,
                "chamber": self.chamber.__json__,
                "printbed": self.printbed.__json__
            },
        }
        return output


class Settings(models.Model):
    name = models.CharField(max_length=20, blank=True)
    pub_date = models.DateTimeField(default=datetime.now, blank=True)
    speed_travel = models.IntegerField(default=140)
    raft_density = models.IntegerField(default=100)
    speed_printing_raft = models.IntegerField(default=0)
    track_height = models.DecimalField(max_digits=3, decimal_places=2, default=0.15)
    track_height_raft = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    track_width = models.DecimalField(max_digits=3, decimal_places=2, default=0.4)
    track_width_raft = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    extrusion_multiplier = models.DecimalField(max_digits=3, decimal_places=2, default=1.0)
    temperature_extruder = models.IntegerField(default=0)
    temperature_extruder_raft = models.IntegerField(default=0)
    retraction_restart_distance = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    retraction_speed = models.IntegerField(default=100)
    retraction_distance = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    bridging_extrusion_multiplier = models.DecimalField(max_digits=3, decimal_places=1, default=1)
    bridging_part_cooling = models.IntegerField(default=0)
    bridging_speed_printing = models.IntegerField(default=0)
    speed_printing = models.IntegerField(default=0)
    coasting_distance = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    critical_overhang_angle = models.IntegerField(default=0)
    temperature_printbed_setpoint = models.IntegerField(default=0)
    temperature_chamber_setpoint = models.IntegerField(default=0)
    part_cooling_setpoint = models.IntegerField(default=0)

    def __str__(self):
        return self.name

    @property
    def __json__(self):
        output = {
            "speed_travel": self.speed_travel,
            "raft_density": self.raft_density,
            "speed_printing_raft": self.speed_printing_raft,
            "track_height": self.track_height,
            "track_height_raft": self.track_height_raft,
            "track_width": self.track_width,
            "track_width_raft": self.track_width_raft,
            "extrusion_multiplier": self.extrusion_multiplier,
            "temperature_extruder": self.temperature_extruder,
            "temperature_extruder_raft": self.temperature_extruder_raft,
            "retraction_restart_distance": self.retraction_restart_distance,
            "retraction_speed": self.retraction_speed,
            "retraction_distance": self.retraction_distance,
            "bridging_extrusion_multiplier": self.bridging_extrusion_multiplier,
            "bridging_part_cooling": self.bridging_part_cooling,
            "bridging_speed_printing": self.bridging_speed_printing,
            "speed_printing": self.speed_printing,
            "coasting_distance": self.coasting_distance,
            "critical_overhang_angle": self.critical_overhang_angle,
            "temperature_printbed_setpoint": self.temperature_printbed_setpoint,
            "temperature_chamber_setpoint": self.temperature_chamber_setpoint,
            "part_cooling_setpoint": self.part_cooling_setpoint
        }
        return output


class Session(models.Model):
    number = models.IntegerField(default=0)
    name = models.CharField(default="Untitled", max_length=20)
    pub_date = models.DateTimeField(default=datetime.now, blank=True)
    target = models.CharField(max_length=20, choices=TARGET_CHOICES, default="mechanical_strength")
    _test_number = models.CharField(max_length=20, choices=TEST_NUMBER_CHOICES, default="01")
    slicer = models.CharField(max_length=20, choices=SLICER_CHOICES, default="Prusa")
    machine = models.ForeignKey(Machine, on_delete=models.CASCADE, null=False)
    material = models.ForeignKey(Material, on_delete=models.CASCADE, null=False)
    settings = models.ForeignKey(Settings, on_delete=models.CASCADE, null=False)

    # Fields that cannot be stored in a DB in any other format
    _min_max_parameter_one = models.CharField(max_length=20, default="[]")
    _min_max_parameter_two = models.CharField(max_length=20, default="[0,0]")
    _min_max_parameter_three = models.CharField(max_length=20, default="[0,0]")
    _persistence = models.TextField(default="", max_length=1000000)
    _previous_tests = models.TextField(default="", max_length=1000000)
    _test_info = models.TextField(default="", max_length=1000000)

    # Temporary storage for persistent printing speed selection
    _printing_speed = models.CharField(default="[0,0]", max_length=20)

    def update_persistence(self):
        """
        Update persistence to represent the current state of child objects.
        :return:
        """
        per = json.loads(self._persistence)
        per["session"] = self.__json__
        per["machine"] = self.machine.__json__
        per["material"] = self.material.__json__
        per["settings"] = self.settings.__json__
        self._persistence = json.dumps(per)
        return json.loads(self._persistence)

    def clean_min_max(self, all_parameters: bool = False, to_zero: bool = False):
        """
        Set min_max_parameter to a nominal value so that they wouldn't be carried over to other tests.
        :param all_parameters:
        :param to_zero:
        :return:
        """
        if to_zero:
            output = [0, 0]
        else:
            output = []
        self.min_max_parameter_one = output
        if all_parameters:
            self.min_max_parameter_two = output
            self.min_max_parameter_three = output

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        self.update_persistence()
        self.settings.save()
        super(Session, self).save(force_insert, force_update, using, update_fields)

    @property
    def persistence(self):
        return self.update_persistence()

    @persistence.setter
    def persistence(self, value):
        if type(value) == dict:
            self._persistence = json.dumps(value)
        else:
            self._persistence = value
        self._previous_tests = self.persistence["session"]["previous_tests"]

    @property
    def min_max_parameter_one(self):
        if type(self._min_max_parameter_one) == list:
            return self._min_max_parameter_one
        else:
            return ast.literal_eval(self._min_max_parameter_one)

    @min_max_parameter_one.setter
    def min_max_parameter_one(self, value):
        self._min_max_parameter_one = str(value)

    @property
    def min_max_parameter_two(self):
        return ast.literal_eval(self._min_max_parameter_two)

    @min_max_parameter_two.setter
    def min_max_parameter_two(self, value):
        self._min_max_parameter_two = str(value)

    @property
    def min_max_parameter_three(self):
        return ast.literal_eval(self._min_max_parameter_three)

    @min_max_parameter_three.setter
    def min_max_parameter_three(self, value):
        self._min_max_parameter_three = str(value)

    def selected_parameter_value(self, value_key, new_value):
        if new_value is not None:
            parameter_numbers = ["parameter_one", "parameter_two", "parameter_three"]
            for number in parameter_numbers:
                if number in value_key:
                    programmatic_name = self.test_info[number]["programmatic_name"]
                    self.settings.__setattr__(programmatic_name, new_value)

                self.alter_previous_tests(-1, value_key, value=new_value)
            self.save()

    @property
    def test_info(self):
        if self._test_info != "":
            temp_info = json.loads(self._test_info)
            if temp_info["test_number"] != self.test_number:
                temp_info = api_client.get_test_info(self.persistence)
            self._test_info = json.dumps(temp_info)
        else:
            temp_info = api_client.get_test_info(self.persistence)
            self._test_info = json.dumps(temp_info)
        self.save()
        return temp_info


    @property
    def get_gcode(self):
        gcode = api_client.return_data(self.persistence, output="gcode")
        self.persistence = api_client.persistence
        return gcode

    @property
    def previous_tests(self):
        return self.persistence["session"]["previous_tests"]

    def alter_previous_tests(self, index, key, value):
        temp_persistence = self.persistence
        temp_persistence["session"]["previous_tests"][index][key] = value
        self.persistence = temp_persistence

    def get_previous_test(self):
        for test in self.previous_tests:
            if test["test_number"] == self.test_number:
                return test

    @property
    def min_max_parameters(self):
        parameters = []
        for item, content in self.test_info.items():
            if item.startswith("parameter_"):
                if type(content) == dict:
                    if content["name"] is None:
                        continue
                    parameters.append({"name": content["name"], "units": content["units"], "iterable_values": list(enumerate(content["values"])),
                                       "values": content["values"], "parameter": item,
                                       "programmatic_name": content["programmatic_name"]})
        return parameters

    @property
    def completed_tests(self):
        return len(self.previous_tests)

    @property
    def executed(self):
        try:
            if self.test_number == self.previous_tests[-1]["test_number"]:
                if self.previous_tests[-1]["test_number"]:
                    return True
            else:
                return False

        except IndexError:
            return False

    def get_validated_tests(self):
        validated_tests = []
        for test in self.previous_tests:
            if test["validated"]:
                validated_tests.append(test["test_number"])
        return validated_tests

    @property
    def test_number(self):
        return self._test_number

    @test_number.setter
    def test_number(self, value):
        if self.test_info["parameter_two"]["name"] == "printing speed":
            self._printing_speed = self.min_max_parameter_two
        self.clean_min_max()
        self._test_number = value

    @property
    def tested_values(self):
        return [self.previous_tests[-1]["tested_parameter_one_values"][::-1], self.previous_tests[-1]["tested_parameter_two_values"]]

    def remove_last_test(self):
        temp_persistence = self.persistence
        del temp_persistence["session"]["previous_tests"][-1]
        self.persistence = temp_persistence
        self.update_persistence()

    def __str__(self):
        return "{} (target: {})".format(self.name, self.target)

    @property
    def __json__(self):
        output = {
            "uid": self.pk,
            "target": self.target,
            "test_number": self.test_number,
            "min_max_parameter_one": self.min_max_parameter_one,
            "min_max_parameter_two": self.min_max_parameter_two,
            "min_max_parameter_three": self.min_max_parameter_three,
            "test_type": "A",
            "user_id": "user name",
            "offset": [
                0,
                0
            ],
            "slicer": self.slicer,
            "previous_tests": json.loads(self._persistence)["session"]["previous_tests"]
        }
        return output


class TestInfo(models.Model):
    test_name = models.CharField(max_length=64, choices=[(x, x) for y, x in TEST_NUMBER_CHOICES])
    test_number = models.CharField(max_length=64, choices=[(y, y) for y, x in TEST_NUMBER_CHOICES])
    executed = models.BooleanField(default=True)

    # Save raw json strings to be serialized/unserialized
    tested_parameter_one_values = models.TextField(max_length=10000, blank=True)
    tested_parameter_two_values = models.TextField(max_length=10000, blank=True)
    tested_parameter_three_values = models.TextField(max_length=10000, blank=True)
    tested_volumetric_flow_rate_values = models.TextField(max_length=10000, blank=True)

    selected_parameter_one_value = models.DecimalField(max_digits=4, decimal_places=3, default=0, blank=True)
    selected_parameter_two_value = models.DecimalField(max_digits=4, decimal_places=3, default=0, blank=True)
    selected_parameter_three_value = models.DecimalField(max_digits=4, decimal_places=3, default=0, blank=True)
    selected_volumetric_flow_rate_value = models.DecimalField(max_digits=4, decimal_places=3, default=0, blank=True)
    parameter_one_name = models.CharField(max_length=64, default="first-layer track height")
    parameter_two_name = models.CharField(max_length=64, default="first-layer printing speed")
    parameter_one_units = models.CharField(max_length=12, choices=UNITS, default="mm")
    parameter_two_units = models.CharField(max_length=12, choices=UNITS, default="mm/s")
    parameter_one_precision = "{:.3f}"
    parameter_two_precision = "{:.1f}"
    comments = 0
    datetime_info = models.DateTimeField(default=datetime.now, blank=True)
    extruded_filament_mm = 841.53
    estimated_printing_time = "0:09:28"
