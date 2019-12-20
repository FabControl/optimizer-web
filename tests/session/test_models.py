from django.contrib.auth import get_user_model
from django.test import TestCase
from session import models
from django.db.models import ForeignKey, ManyToOneRel
from unittest.mock import Mock, patch
import re

class SessionModelsTest(TestCase):
    @classmethod
    def setUpClass(self):
        self.user = get_user_model().objects.create_user(email='known_user@somewhere.com',
                                 is_active=True,
                                 password='SomeSecretPassword')

        self.machine = models.Machine.objects.create(owner=self.user,
                model='SessionModelTest Machine',
                buildarea_maxdim1 = 200,
                buildarea_maxdim2 = 220,
                form='eliptic',
                extruder_type='directdrive',
                extruder=models.Extruder.objects.create(
                    temperature_max=400,
                    tool='T1',
                    nozzle=models.Nozzle.objects.create(size_id=0.7)),
                chamber=models.Chamber.objects.create(temperature_max=100),
                printbed=models.Printbed.objects.create(temperature_max=90)
                )

    @classmethod
    def tearDownClass(self):
        self.user.delete()

    def assertCopiedMachine(self, orig, copied):
        self.assertEqual(orig.owner, self.user)
        self.assertEqual(copied.owner, None)

        self.assertEqual(orig.model, copied.model)
        self.assertEqual(orig.buildarea_maxdim1, copied.buildarea_maxdim1)
        self.assertEqual(orig.buildarea_maxdim2, copied.buildarea_maxdim2)
        self.assertEqual(orig.form, copied.form)
        self.assertEqual(orig.extruder_type, copied.extruder_type)

        self.assertTrue(orig.pk != copied.pk)
        self.assertTrue(orig.extruder != copied.extruder)
        self.assertTrue(orig.chamber != copied.chamber)
        self.assertTrue(orig.printbed != copied.printbed)

        # compare printbeds
        self.assertEqual(orig.printbed.printbed_heatable, copied.printbed.printbed_heatable)
        self.assertEqual(orig.printbed.temperature_max, copied.printbed.temperature_max)

        # compare chambers
        self.assertEqual(orig.chamber.chamber_heatable, copied.chamber.chamber_heatable)
        self.assertEqual(orig.chamber.tool, copied.chamber.tool)
        self.assertEqual(orig.chamber.gcode_command, copied.chamber.gcode_command)
        self.assertEqual(orig.chamber.temperature_max, copied.chamber.temperature_max)

        # compare extrueders
        self.assertTrue(orig.extruder.nozzle != copied.extruder.nozzle)
        self.assertEqual(orig.extruder.temperature_max, copied.extruder.temperature_max)
        self.assertEqual(orig.extruder.tool, copied.extruder.tool)
        self.assertEqual(orig.extruder.part_cooling, copied.extruder.part_cooling)

        # compare nozzles
        self.assertEqual(orig.extruder.nozzle.size_id, copied.extruder.nozzle.size_id)


    def test_machine_copyable(self):
        # DON'T COPY self.machine DIRECTLY, BECAUSE YOU LOSE REFERENCE TO IT
        machine1 = models.Machine.objects.get(pk=self.machine.pk).save_as_copy()

        # just to be sure, that instance reflects data in db
        machine1 = models.Machine.objects.get(pk=machine1.pk)

        self.machine.refresh_from_db()

        # compare machines
        self.assertCopiedMachine(self.machine, machine1)

        # assign user to check deletion correctness
        machine1.owner = self.user
        machine1.save()
        # make sure deletion works recursively
        machine1.delete()
        removed_instances = (machine1,
                             machine1.chamber,
                             machine1.extruder,
                             machine1.printbed,
                             machine1.extruder.nozzle)

        for obj in removed_instances:
            instances = type(obj).objects.filter(pk=obj.pk)
            self.assertEqual(len(instances), 0, msg='{} was not deleted'.format(obj))

        # original machine should still be in db
        leftover_instances = (self.machine,
                             self.machine.chamber,
                             self.machine.extruder,
                             self.machine.printbed,
                             self.machine.extruder.nozzle,
                             self.user)

        for obj in leftover_instances:
            instances = type(obj).objects.filter(pk=obj.pk)
            self.assertEqual(len(instances), 1, msg='{} was deleted'.format(obj))

