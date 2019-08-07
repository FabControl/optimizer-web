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


class Session(models.Model):
    number = models.IntegerField(default=0)
    name = models.CharField(default="Untitled", max_length=20)
    pub_date = models.DateTimeField(default=datetime.now, blank=True)
    target = models.CharField(max_length=20, choices=TARGET_CHOICES, default="MS")
    test_number = models.CharField(max_length=20, choices=TEST_NUMBER_CHOICES, default="01")
    slicer = models.CharField(max_length=20, choices=SLICER_CHOICES, default="Prusa")
    machine = models.ForeignKey(Machine, on_delete=models.SET_NULL, null=True)
    material = models.ForeignKey(Material, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return "{} (target: {})".format(self.name, self.target)


class Settings(models.Model):
    name = models.CharField(max_length=20, blank=True)
    pub_date = models.DateTimeField(default=datetime.now, blank=True)

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
