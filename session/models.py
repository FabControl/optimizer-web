from django.db import models

# Create your models here.


class Material(models.Model):
    size_od = models.DecimalField(default=1.75, max_digits=3, decimal_places=2)
    name = models.CharField(max_length=60)
    pub_date = models.DateTimeField('date published', auto_now_add=True)

    def __str__(self):
        return "{} ({} mm)".format(self.name, str(self.size_od))


class Chamber(object):
    def __init__(self, tool, gcode_command="M141 S$temp", temperature_max=80):
        self.tool = tool
        self.gcode_command = gcode_command
        self.temprature_max = temperature_max


class Machine(models.Model):
    model = models.CharField(max_length=30, default="Unknown")
    buildarea_maxdim1 = models.IntegerField(default=0)
    buildarea_maxdim2 = models.IntegerField(default=0)

    FORM_CHOICES = [("elliptic", "Elliptic"), ("cartesian", "Cartesian")]
    form = models.CharField(max_length=20, choices=FORM_CHOICES, default="cartesian")

    TOOL_CHOICES = [("T0", "T0"), ("T1", "T1"), ("T2", "T2")]
    chamber = Chamber(tool=models.CharField(max_length=3, choices=TOOL_CHOICES, default="T0"))

    def __str__(self):
        return self.model


class Session(models.Model):
    session_number = models.IntegerField(default=0)
    TARGET_CHOICES = [("MS", "Mechanical Strength"), ("A", "Aesthetics"), ("FP", "Fast Printing")]
    target = models.CharField(max_length=20, choices=TARGET_CHOICES, default="MS")
    TEST_NUMBER_CHOICES = [("01", "First-layer printing height test"), ("03", "Extrusion temperature test")]
    test_number = models.CharField(max_length=20, choices=TEST_NUMBER_CHOICES, default="01")
    SLICER_CHOICES = [("Prusa", "Slic3r PE"), ("Simplify3D", "Simplify3D"), ("Cura", "Cura")]
    slicer = models.CharField(max_length=20, choices=SLICER_CHOICES, default="Prusa")

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
