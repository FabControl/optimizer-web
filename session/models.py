import ast
import logging
import simplejson as json
from django.db import models
from django.utils import timezone
from django.http import Http404
from django.conf import settings
from authentication.models import User
from optimizer_api import api_client
from .choices import TEST_NUMBER_CHOICES, TARGET_CHOICES, SLICER_CHOICES, TOOL_CHOICES, FORM_CHOICES, UNITS

# Create your models here.

PREVENT_DELETION_MODELS = (User,)


def recursive_delete(instance, using=None, keep_parents=False):
    foreign = (x for x in instance._meta.get_fields() if isinstance(x, models.ForeignKey))

    for f in foreign:
        v = getattr(instance, f.name)
        if v is not None:
            if any(isinstance(v, x) for x in PREVENT_DELETION_MODELS):
                continue
            recursive_delete(v, using, keep_parents)
    models.Model.delete(instance, using, keep_parents)


class DependenciesCopyMixin():
    # Should not leak database space, because:
    # 1. copied instances have owner set to None
    # 2. instances with owner == None are skipped
    def copy_dependencies(self, save=True):
        # create copy of all ForeignKey instances
        foreign = (x for x in self._meta.get_fields() if isinstance(x, models.ForeignKey))

        for f in foreign:
            v = getattr(self, f.name)
            if v is not None:
                if hasattr(v, 'owner'):
                    if v.owner == None:
                        continue
                if isinstance(v, CopyableModelMixin):
                    setattr(self, f.name, v.save_as_copy())

        if save:
            self.save()


class CopyableModelMixin(DependenciesCopyMixin):
    def save_as_copy(self):
        # this method "hides" new copy of model instance from user
        self.pk = None
        if hasattr(self, 'owner'):
            self.owner = None
        self.copy_dependencies()
        return self


class Material(models.Model, CopyableModelMixin):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    corporation = models.ForeignKey('payments.Corporation', on_delete=models.CASCADE, null=True)
    size_od = models.DecimalField(default=1.75, max_digits=3, decimal_places=2)
    name = models.CharField(max_length=60)
    notes = models.CharField(max_length=240, null=True)
    pub_date = models.DateTimeField(default=timezone.now, blank=True)

    def is_owner(self, user: User):
        """
            Checks whether instance.owner is a supplied user. Returns 403 if it isn't.
            :param user:
            :return:
            """
        if self.owner != user:
            raise Http404
        else:
            return True

    def __str__(self):
        return "{} ({} mm)".format(self.name, str(self.size_od))

    @property
    def __json__(self):
        output = {
            "size_od": self.size_od,
            "name": self.name
        }
        return output


class Nozzle(models.Model, CopyableModelMixin):
    size_id = models.DecimalField(default=0.4, decimal_places=2, max_digits=3)

    @property
    def __json__(self):
        output = {
            "size_id": self.size_id
        }
        return output


class Extruder(models.Model, CopyableModelMixin):
    pub_date = models.DateTimeField(default=timezone.now, blank=True)

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


class Chamber(models.Model, CopyableModelMixin):
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


class Printbed(models.Model, CopyableModelMixin):
    printbed_heatable = models.BooleanField(default=True)
    temperature_max = models.IntegerField(default=120)

    @property
    def __json__(self):
        output = {
            "printbed_heatable": self.printbed_heatable,
            "temperature_max": self.temperature_max
        }
        return output


class Machine(models.Model, CopyableModelMixin):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    corporation = models.ForeignKey('payments.Corporation', on_delete=models.CASCADE, null=True)
    pub_date = models.DateTimeField(default=timezone.now, blank=True)
    model = models.CharField(max_length=30, default="Unknown")
    buildarea_maxdim1 = models.IntegerField(default=0)
    buildarea_maxdim2 = models.IntegerField(default=0)
    form = models.CharField(max_length=20, choices=FORM_CHOICES, default="cartesian")
    extruder = models.ForeignKey(Extruder, on_delete=models.CASCADE)
    chamber = models.ForeignKey(Chamber, on_delete=models.CASCADE, blank=True)
    printbed = models.ForeignKey(Printbed, on_delete=models.CASCADE, blank=True)
    extruder_type = models.CharField(max_length=20, choices=(('bowden', 'Bowden'), ('directdrive', 'Direct drive')), default='bowden')
    gcode_header = models.TextField(default='')
    gcode_footer = models.TextField(default='G28 ; Move to home position\nM84 ; Disable motors')
    homing_sequence = models.TextField(default='G28 ; Move to home position')
    offset_1 = models.DecimalField(default=0, max_digits=5, decimal_places=2)
    offset_2 = models.DecimalField(default=0, max_digits=5, decimal_places=2)

    def delete(self, using=None, keep_parents=False):
        return recursive_delete(self, using, keep_parents)

    def __str__(self):
        return "{} ({} mm)".format(self.model, str(self.extruder.nozzle.size_id))

    def is_owner(self, user: User):
        """
            Checks whether instance.owner is a supplied user. Returns 403 if it isn't.
            :param user:
            :return:
            """
        if self.owner != user:

            raise Http404
        else:
            return True

    @property
    def __json__(self):
        output = {
            "model": self.model,
            "buildarea_maxdim1": self.buildarea_maxdim1,
            "buildarea_maxdim2": self.buildarea_maxdim2,
            "form": self.form,
            "extruder_type": self.extruder_type,
            "gcode_header": self.gcode_header,
            "gcode_footer": self.gcode_footer,
            "homing_sequence": self.homing_sequence,
            "temperature_controllers": {
                "extruder": self.extruder.__json__,
                "chamber": self.chamber.__json__,
                "printbed": self.printbed.__json__
            },
        }
        return output


class Settings(models.Model):
    name = models.CharField(max_length=20, blank=True)
    pub_date = models.DateTimeField(default=timezone.now, blank=True)
    speed_travel = models.IntegerField(default=140)
    raft_density = models.IntegerField(default=100)
    speed_printing_raft = models.IntegerField(default=0)
    track_height = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    track_height_raft = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    track_width = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    track_width_raft = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    extrusion_multiplier = models.DecimalField(max_digits=3, decimal_places=2, default=1.0)
    _temperature_extruder = models.IntegerField(default=0)
    temperature_extruder_raft = models.IntegerField(default=0)
    retraction_restart_distance = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    retraction_speed = models.IntegerField(default=0)
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
    def temperature_extruder(self):
        """
        If temperature_extruder is 0, default to temperature_extruder_raft
        :return:
        """
        if self._temperature_extruder == 0:
            self._temperature_extruder = self.temperature_extruder_raft
            self.save()
        return self._temperature_extruder

    @temperature_extruder.setter
    def temperature_extruder(self, value):
        """
        Stores actual value to the DB via a hidden variable
        :param value:
        :return:
        """
        self._temperature_extruder = value

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


class Session(models.Model, DependenciesCopyMixin):
    """
    Used to store testing session progress, relevant assets (machine, material) and test data.
    """
    number = models.IntegerField(default=0)
    name = models.CharField(default="Untitled", max_length=20)
    corporation = models.ForeignKey('payments.Corporation', on_delete=models.CASCADE, null=True)
    pub_date = models.DateTimeField(default=timezone.now, blank=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
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
    _previously_tested_parameters = models.TextField(default="{}", max_length=1000000)

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
        return per

    def is_owner(self, user: User):
        """
            Checks whether instance.owner is a supplied user. Returns 403 if it isn't.
            :param user:
            :return:
            """
        if self.owner != user:
            raise Http404
        else:
            return True

    def init_settings(self):
        """
        Initializes settings and sets some initial values for certain fields with machine-specific values.
        :return:
        """
        for name, value in self.persistence["settings"].items():
            self.settings.__setattr__(name, value)
        self.settings.track_width_raft = self.machine.extruder.nozzle.size_id
        self.settings.track_width = self.machine.extruder.nozzle.size_id
        self.settings.track_height_raft = float(self.machine.extruder.nozzle.size_id) * 0.6
        self.settings.speed_printing_raft = 15
        if self.machine.extruder_type.strip().lower() == 'bowden':
            self.settings.retraction_speed = 100
        else:
            self.settings.retraction_speed = 30

    def clean_min_max(self, to_zero: bool = False):
        """
        Set min_max_parameter to a nominal value so that they wouldn't be carried over to other tests.
        :param to_zero:
        :return:
        """

        for parameter in self.min_max_parameters:
            if "speed_printing" not in parameter["programmatic_name"]:
                if to_zero:
                    output = [0, 0]
                else:
                    output = []
            else:
                output = self.get_last_min_max_speed()
            names = [param["programmatic_name"] for param in self.min_max_parameters]
            if parameter["parameter"].endswith("one"):
                self.min_max_parameter_one = output
            elif parameter["parameter"].endswith("two"):
                self.min_max_parameter_two = output
            elif parameter["parameter"].endswith("three"):
                self.min_max_parameter_three = output

    def delete(self, using=None, keep_parents=False):
        return recursive_delete(self, using, keep_parents)

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        """
        Saves self, as well as self.settings upon saving.
        :param force_insert:
        :param force_update:
        :param using:
        :param update_fields:
        :return:
        """
        self.copy_dependencies(save=False)
        self.update_persistence()
        self.settings.save()
        super(Session, self).save(force_insert, force_update, using, update_fields)

    @property
    def persistence(self):
        """
        Updates and then returns a Session persistent data dictionary.
        :return:
        """
        return self.update_persistence()

    @persistence.setter
    def persistence(self, value: dict or str):
        """
        Sets persistent data dictionary and self.settings fields to input value.
        :param value:
        :return:
        """
        if type(value) == dict:
            self.settings.critical_overhang_angle = value["settings"]["critical_overhang_angle"]
            self.settings.save()
            self._persistence = json.dumps(value)
        else:
            self._persistence = value
        self._previous_tests = self.persistence["session"]["previous_tests"]

    @property
    def min_max_parameter_one(self):
        """
        Deserializes self._min_max_parameter_one to a list of two values.
        :return:
        """
        if type(self._min_max_parameter_one) == list:
            return self._min_max_parameter_one
        else:
            return ast.literal_eval(self._min_max_parameter_one)

    @min_max_parameter_one.setter
    def min_max_parameter_one(self, value):
        """
        Serializes input value to self._min_max_parameter_one as a string.
        :return:
        """
        if type(value) != list:
            raise TypeError("Given input value {} is not a list.".format(str(value)))
        self._min_max_parameter_one = str(value)

    @property
    def min_max_parameter_two(self):
        """
        Deserializes self._min_max_parameter_two to a list of two values.
        :return:
        """
        return ast.literal_eval(self._min_max_parameter_two)

    @min_max_parameter_two.setter
    def min_max_parameter_two(self, value):
        """
        Serializes input value to self._min_max_parameter_two as a string.
        :return:
        """
        self._min_max_parameter_two = str(value)

    @property
    def min_max_parameter_three(self):
        """
        Deserializes self._min_max_parameter_three to a list of two values.
        :return:
        """
        return ast.literal_eval(self._min_max_parameter_three)

    @min_max_parameter_three.setter
    def min_max_parameter_three(self, value):
        """
        Serializes input value to self._min_max_parameter_three as a string.
        :return:
        """
        self._min_max_parameter_three = str(value)

    def selected_parameter_value(self, value_key, new_value):
        """
        Assigns newly selected settings to self.settings object.
        For example, user selects track_height of 0.15, and this will set self.settings.track_height to 0.15
        :param value_key:
        :param new_value:
        :return:
        """
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
        """
        Checks if test_info is cached and if it is still valid for the current test.
        If it isn't, test_info is updated.
        :return:
        """
        temp_info = None
        if self._test_info != "":
            temp_info = json.loads(self._test_info)
            if temp_info["test_number"] != self.test_number:
                self.update_test_info()
            self._test_info = json.dumps(temp_info)
        else:
            self.update_test_info()
        self.save()
        return temp_info

    def update_test_info(self):
        """
        Contacts Optimizer API to retrieve test_info for the current persistence data.
        :return:
        """
        temp_info = api_client.get_test_info(self.persistence)
        self._test_info = json.dumps(temp_info)
        return temp_info

    @property
    def get_gcode(self):
        """
        Retrieves GCODE for the current persistence data.
        :return:
        """
        gcode = api_client.return_data(self.persistence, output="gcode")
        self.persistence = api_client.persistence
        return gcode

    @property
    def previous_tests(self):
        """
        A shortcut method for retrieving a list of dicts of previous test data.
        :return:
        """
        return self.persistence["session"]["previous_tests"]

    def previous_tests_as_dict(self):
        """
        A shortcut method for retrieving a dict of dicts of previous test data.
        Follows the convention of test_number: {test data}
        :return:
        """
        output = {}
        for test in self.previous_tests:
            output[test["test_number"]] = test
        return output

    def alter_previous_tests(self, index, key, value):
        """
        A method which takes a test index, field key and value, to manually alter fields in formerly tested tests.
        :param index:
        :param key:
        :param value:
        :return:
        """
        temp_persistence = self.persistence
        temp_persistence["session"]["previous_tests"][index][key] = value
        self.persistence = temp_persistence

    def delete_previous_test(self, number):
        """
        Deletes test (or tests) from self.previous_tests, if their test_number == number
        :param number:
        :return:
        """
        persistence = self.persistence
        temp_tests = self.previous_tests
        for test in temp_tests:
            if test["test_number"] == number:
                temp_tests.remove(test)
        persistence["session"]["previous_tests"] = temp_tests
        self.persistence = persistence

    def get_test_with_current_number(self):
        """
        Looks through previous tests and returns data of the first test whose number matches the current self.test_number.
        :return:
        """
        for test in self.previous_tests:
            if test["test_number"] == self.test_number:
                return test

    @property
    def min_max_parameters(self):
        """
        Returns a list of dicts (or dict) of min_max parameters (one, two or three)
        :return:
        """
        parameters = []
        for item, content in self.test_info.items():
            if item.startswith("parameter_"):
                if type(content) == dict:
                    if content["name"] is None:
                        continue
                    parameters.append({"name": content["name"], "units": content["units"],
                                       "iterable_values": list(enumerate(content["values"])),
                                       "values": content["values"], "parameter": item,
                                       "programmatic_name": content["programmatic_name"],
                                       "min_max": content["min_max"],
                                       "hint_active": content["hint_active"],
                                       "active": content["active"]})
        if len(parameters) == 3:
            parameters = [parameters[i] for i in [0, 2, 1]]
        return parameters

    def get_last_min_max_speed(self):
        """
        Attempts to return the previously used min_max speed, returns [0,0] if doesn't find any.
        :return:
        """
        for test in self.previous_tests[::-1]:
            for i in range(len(test["tested_parameters"])):
                parameter = test["tested_parameters"][i]
                if parameter["programmatic_name"] is None: continue
                if "speed_printing" in parameter["programmatic_name"]:
                    selected = test['selected_parameter_{}_value'.format(
                                                    ('one','two','three')[i])]
                    return [selected, selected * 2]

        return [0, 0]

    @property
    def completed_tests(self):
        """
        Returns the amount of previously conducted tests.
        :return:
        """
        return len(self.previous_tests)

    @property
    def executed(self):
        """
        Checks whether or not the current test is executed. Used to trigger validation view.
        :return:
        """
        try:
            for test in self.previous_tests:
                if self.test_number == test["test_number"] and test["executed"]:
                    return True
            return False
        except IndexError:
            return False

    def get_validated_tests(self):
        """
        Returns a list of test data for tests that have been validated.
        :return:
        """
        validated_tests = []
        for test in self.previous_tests:
            if test["validated"]:
                validated_tests.append(test["test_number"])
        return validated_tests

    @property
    def test_number(self):
        """
        Returns the current/active test number
        :return:
        """
        return self._test_number

    @test_number.setter
    def test_number(self, value):
        """
        Sets the active test number to the new one, checks whether or not the test is available for the user,
        advances to the next primary test if it isn't.
        Flushes test_info and min_max parameters.
        :param value:
        :return:
        """
        time_limited_plans = settings.TIME_LIMITED_PLANS
        allowed_numbers = []
        if self.owner.plan == 'basic':
            allowed_numbers = settings.FREE_TESTS
        elif self.owner.plan in time_limited_plans:
            allowed_numbers = [number for number in api_client.get_routine(mode='full')]
        if value in allowed_numbers:
            self._test_info = ""
            self._test_number = value
            self.update_test_info()
            self.clean_min_max()
        else:
            self.test_number = self.test_number_next()
            self.save()
            logging.getLogger("views").info("{} tried to set a disallowed test_number".format(self.owner))

    @property
    def completed(self):
        tests = self.previous_tests
        if len(tests) < 1 or not self.executed:
            print(self, 'test not executed, so can not be completed')
            return False
        result = self.test_number == self.test_number_next() and tests[-1]['validated']
        return result

    def test_number_next(self, primary: bool = True):
        """
        Method for advancing test_number according to testing session routine retrieved from backend
        :return:
        """
        routine = api_client.get_routine()
        test_names = [name for name, _ in routine.items()]

        next_test = None
        next_primary_test = None

        current_found = False
        for i, test_info in enumerate(routine.items()):
            if current_found:
                if test_info[1]["priority"] == "primary":
                    next_primary_test = test_names[i]
                    break
            if test_info[0] == self.test_number:
                try:
                    next_test = test_names[i + 1]
                except IndexError:
                    next_primary_test = next_test = self.test_number
                current_found = True
        if primary:
            if next_primary_test in settings.FREE_TESTS:
                return next_primary_test
            else:
                return self.test_number
        else:
            return next_test

    @property
    def tested_values(self):
        """
        Returns a list of tested_parameters (one and two). One is inverted.
        Used in validation table.
        :return:
        """
        t = self.previous_tests[-1]
        return [t["tested_parameter_one_values"][::-1],
                t["tested_parameter_two_values"]]

    @property
    def tested_value_units(self):
        """
        Returns a list of tested_parameter_units (one and two).
        Used in validation table.
        :return:
        """
        t = self.previous_tests[-1]
        return [t["parameter_one_units"],
                t["parameter_two_units"]]

    @property
    def previously_tested_parameters(self):
        """
        Returns a dict of lists of previously tested and set parameters.
        Follows the following convention ["test_number"][parameter1, parameter2, ...]
        :return:
        """
        return json.loads(self._previously_tested_parameters)

    @previously_tested_parameters.setter
    def previously_tested_parameters(self, value):
        """
        Takes a list of parameters and assigns it to current test number key in self._previously_test_values
        Used to block previously tested and assigned values in test generation view.
        :param value:
        :return:
        """
        parameters = self.previously_tested_parameters
        if value is not None:
            parameters[self.test_number] = value
        else:
            del parameters[self.test_number]
        self._previously_tested_parameters = json.dumps(parameters)

    def get_previously_tested_parameters(self):
        """
        Returns a flat list of previously tested and/or assigned parameters.
        Follows the convention of [parameter1, parameter2, parameter3, ...]
        :return:
        """
        parameters = self.previously_tested_parameters
        previous_tests = self.previous_tests_as_dict()
        output = []
        for test, param_list in parameters.items():
            if test in previous_tests:
                if previous_tests[test]['validated']:
                    for param in param_list:
                        if param not in output:
                            output.append(param)
        return output

    def remove_last_test(self):
        """
        Delete the last test in previous_tests. Used to undo a test_generation from test validation_view.
        :return:
        """
        temp_persistence = self.persistence
        del temp_persistence["session"]["previous_tests"][-1]
        self.persistence = temp_persistence
        self.update_persistence()

    def __str__(self):
        return "{} (target: {})".format(self.name, self.target)

    @property
    def __json__(self) -> dict:
        """
        Returns ["session"] persistent data block representation of the current session state.
        :return: type dict
        """
        user = " ".join([self.owner.first_name, self.owner.last_name]) if self.owner is not None else 'user name'
        output = {
            "uid": self.pk,
            "target": self.target,
            "test_number": self.test_number,
            "min_max_parameter_one": self.min_max_parameter_one,
            "min_max_parameter_two": self.min_max_parameter_two,
            "min_max_parameter_three": self.min_max_parameter_three,
            "test_type": "A",
            "user_id": user,
            "offset": [
                self.machine.offset_1,
                self.machine.offset_2
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
    datetime_info = models.DateTimeField(default=timezone.now, blank=True)
    extruded_filament_mm = 841.53
    estimated_printing_time = "0:09:28"
