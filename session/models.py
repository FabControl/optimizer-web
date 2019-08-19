from django.db import models
from datetime import datetime
from .choices import TEST_NUMBER_CHOICES, TARGET_CHOICES, SLICER_CHOICES, TOOL_CHOICES, FORM_CHOICES

# Create your models here.
class Material(models.Model):
    size_od = models.DecimalField(default=1.75, max_digits=3, decimal_places=2)
    name = models.CharField(max_length=60)
    pub_date = models.DateTimeField(default=datetime.now, blank=True)

    def __str__(self):
        return "{} ({} mm)".format(self.name, str(self.size_od))


class Nozzle(models.Model):
    size_id = models.DecimalField(default=0.4, decimal_places=1, max_digits=2)


class Extruder(models.Model):
    name = models.CharField(max_length=20)
    pub_date = models.DateTimeField(default=datetime.now, blank=True)

    tool = models.CharField(choices=TOOL_CHOICES, max_length=3, blank=True, default="T0")
    temperature_max = models.IntegerField(default=350)
    part_cooling = models.BooleanField(default=True)
    nozzle = models.ForeignKey(Nozzle, on_delete=models.CASCADE)
    
    #       "extruder": {
    #         "tool": "",
    #         "temperature_max": 350,
    #         "part_cooling": true,
    #         "nozzle": {
    #           "size_id": 0.8
    #         }


class Chamber(models.Model):
    chamber_heatable = models.BooleanField(default=False)
    tool = models.CharField(max_length=3, choices=TOOL_CHOICES, blank=True)
    gcode_command = models.CharField(max_length=40, default="M141 S$temp")
    temperature_max = models.IntegerField(default=80)
    #       "chamber": {
    #         "tool": "",
    #         "gcode_command": "M141 S$temp",
    #         "temperature_max": 80,
    #         "chamber_heatable": false
    #       },


class Printbed(models.Model):
    printbed_heatable = models.BooleanField(default=True)
    # "printbed": {
    #         "printbed_heatable": true
    #       }


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

    def __str__(self):
        return "{} (target: {})".format(self.name, self.target)


# class Test(models.Model):
#     test_name = models.CharField(max_length=64, choices=[(x, x) for y, x in TEST_NUMBER_CHOICES])
#     test_number = models.CharField(max_length=64, choices=[(y, y) for y, x in TEST_NUMBER_CHOICES])
#     executed = models.BooleanField(default=True)
#     tested_parameter_one_values = None
#     tested_parameter_two_values = None
#     tested_parameter_three_values = None
#     tested_volumetric_flow_rate_values = None
#     selected_parameter_one_value = models.DecimalField(max_digits=4, decimal_places=3, default=0, blank=True)
#     selected_parameter_two_value = models.DecimalField(max_digits=4, decimal_places=3, default=0, blank=True)
#     selected_parameter_three_value = models.DecimalField(max_digits=4, decimal_places=3, default=0, blank=True)
#     selected_volumetric_flow_rate_value = models.DecimalField(max_digits=4, decimal_places=3, default=0, blank=True)
#     # "selected_parameter_one_value": 0.375,
#     # "selected_parameter_two_value": 25,
#     # "selected_volumetric_flow-rate_value": 8.432,
#     # "parameter_one_name": "first-layer track height",
#     # "parameter_two_name": "first-layer printing speed",
#     # "parameter_one_units": "mm",
#     # "parameter_two_units": "mm/s",
#     # "parameter_one_precision": "{:.3f}",
#     # "parameter_two_precision": "{:.1f}",
#     # "gcode_path": "G:\\3d_printing\\Procedure\\OOP\\mp-testing-suite-v2\\gcodes\\212_01.gcode",
#     # "label_path": "G:\\3d_printing\\Procedure\\OOP\\mp-testing-suite-v2\\pngs\\212_01.png",
#     # "comments": 0,
#     # "datetime_info": "2019-07-18 09:15:06",
#     # "extruded_filament_mm": 841.53,
#     # "estimated_printing_time": "0:09:28"


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
