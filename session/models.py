from django.db import models

# Create your models here.


class Material(models.Model):
    size_od = models.DecimalField(max_digits=3, decimal_places=2)
    name = models.CharField(max_length=60)

    def __str__(self):
        return "{} ({} mm)".format(self.name, str(self.size_od))


class Machine(models.Model):
    model = models.CharField(max_length=30)
    buildarea_maxdim1 = models.IntegerField()
    buildarea_maxdim2 = models.IntegerField()

    FORM_CHOICES = [("elliptic", "Elliptic"), ("cartesian", "Cartesian")]
    form = models.CharField(max_length=20, choices=FORM_CHOICES, default="Cartesian")

    def __str__(self):
        return self.model






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