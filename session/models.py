from django.db import models
from datetime import datetime
from .choices import TEST_NUMBER_CHOICES, TARGET_CHOICES, SLICER_CHOICES, TOOL_CHOICES, FORM_CHOICES, UNITS
from django.conf import settings
from optimizer_api import ApiClient

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
    name = models.CharField(max_length=20)
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
                "extruder": self.extruder.__json__
            },
            "chamber": self.chamber.__json__,
            "printbed": self.printbed.__json__
        }
        return output


class Settings(models.Model):
    name = models.CharField(max_length=20, blank=True)
    pub_date = models.DateTimeField(default=datetime.now, blank=True)

    min_max_parameter_one_min = models.DecimalField(default=0, max_digits=3, decimal_places=2)
    min_max_parameter_one_max = models.DecimalField(default=0, max_digits=3, decimal_places=2)
    min_max_parameter_two_min = models.IntegerField(default=0)
    min_max_parameter_two_max = models.IntegerField(default=0)

    speed_travel = models.IntegerField(default=140)
    raft_density = models.IntegerField(default=100)
    speed_printing_raft = models.IntegerField(default=25)
    track_height = models.DecimalField(max_digits=3, decimal_places=2, default=0.2)
    track_height_raft = models.DecimalField(max_digits=3, decimal_places=2, default=0.2)
    track_width = models.DecimalField(max_digits=3, decimal_places=2, default=0.3)
    track_width_raft = models.DecimalField(max_digits=3, decimal_places=2, default=0.3)
    extrusion_multiplier = models.DecimalField(max_digits=3, decimal_places=2, default=1.0)
    temperature_extruder = models.IntegerField(default=260)
    temperature_extruder_raft = models.IntegerField(default=260)
    retraction_restart_distance = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    retraction_speed = models.IntegerField(default=100)
    retraction_distance = models.DecimalField(max_digits=4, decimal_places=2, default=2.6)
    bridging_extrusion_multiplier = models.DecimalField(max_digits=3, decimal_places=1, default=1)
    bridging_part_cooling = models.IntegerField(default=100)
    bridging_speed_printing = models.IntegerField(default=40)
    speed_printing = models.IntegerField(default=80)
    coasting_distance = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    critical_overhang_angle = models.IntegerField(default=53.0)
    temperature_printbed_setpoint = models.IntegerField(default=90)
    temperature_chamber_setpoint = models.IntegerField(default=80)
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
            "temperature_chamber_setpoint": self.temperature_printbed_setpoint,
            "part_cooling_setpoint": self.part_cooling_setpoint
        }
        return output


class Session(models.Model):
    number = models.IntegerField(default=0)
    name = models.CharField(default="Untitled", max_length=20)
    pub_date = models.DateTimeField(default=datetime.now, blank=True)
    target = models.CharField(max_length=20, choices=TARGET_CHOICES, default="mechanical_strength")
    test_number = models.CharField(max_length=20, choices=TEST_NUMBER_CHOICES, default="01")
    slicer = models.CharField(max_length=20, choices=SLICER_CHOICES, default="Prusa")
    machine = models.ForeignKey(Machine, on_delete=models.CASCADE, null=False)
    material = models.ForeignKey(Material, on_delete=models.CASCADE, null=False)
    settings = models.ForeignKey(Settings, on_delete=models.CASCADE, null=False)

    def save(self, **kwargs):
        super(Session, self).save(**kwargs)

    def __str__(self):
        return "{} (target: {})".format(self.name, self.target)

    @property
    def __json__(self):
        output = {
            "machine": self.machine.__json__,
            "material": self.material.__json__,
            "session": {
                "uid": 211,
                "target": self.target,
                "test_number": "03",
                "min_max_parameter_one": [],
                "min_max_parameter_two": [
                    40,
                    100
                ],
                "min_max_parameter_three": [],
                "test_type": "A",
                "user_id": "user name",
                "offset": [
                    0,
                    0
                ],
                "slicer": self.slicer,
                "previous_tests": []
            },
            "settings": self.settings.__json__
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


# {
#   "machine": {
#     "model": "model name",
#     "buildarea_maxdim1": 200,
#     "buildarea_maxdim2": 200,
#     "form": "elliptic",
#     "temperature_controllers": {
#       "extruder": {
#         "tool": "",
#         "temperature_max": 350,
#         "part_cooling": true,
#         "nozzle": {
#           "size_id": 0.8
#         }
#       },
#       "chamber": {
#         "tool": "",
#         "gcode_command": "M141 S$temp",
#         "temperature_max": 80,
#         "chamber_heatable": false
#       },
#       "printbed": {
#         "printbed_heatable": true
#       }
#     }
#   },
#   "material": {
#     "size_od": 1.75,
#     "name": "material name"
#   },
#   "session": {
#     "uid": 211,
#     "target": "mechanical_strength",
#     "test_number": "03",
#     "min_max_parameter_one": [],
#     "min_max_parameter_two": [
#       40,
#       100
#     ],
#     "min_max_parameter_three": [],
#     "test_type": "A",
#     "user_id": "user name",
#     "offset": [
#       0,
#       0
#     ],
#     "slicer": "prusa slic3r",
#     "previous_tests": []
#   },
#   "settings": {
#     "speed_travel": 140,
#     "raft_density": 100,
#     "speed_printing_raft": 25,
#     "track_height": 0.2,
#     "track_height_raft": 0.2,
#     "track_width": 0.3,
#     "track_width_raft": 0.3,
#     "extrusion_multiplier": 1.0,
#     "temperature_extruder": 260,
#     "temperature_extruder_raft": 260,
#     "retraction_restart_distance": 0,
#     "retraction_speed": 100,
#     "retraction_distance": 2.6,
#     "bridging_extrusion_multiplier": 1,
#     "bridging_part_cooling": 100,
#     "bridging_speed_printing": 40,
#     "speed_printing": 80,
#     "coasting_distance": 0,
#     "critical_overhang_angle": 53.0,
#     "temperature_printbed_setpoint": 90,
#     "temperature_chamber_setpoint": 80,
#     "part_cooling_setpoint": 0
#   }
# }
