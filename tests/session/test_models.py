from django.contrib.auth import get_user_model
from django.test import TestCase
from session import models
from django.db.models import ForeignKey, ManyToOneRel
from unittest.mock import Mock, patch
import re
from .testing_helpers import BLANK_PERSISTENCE, assertMachinesEqual
import json

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
                gcode_header = 'This is test machine specific header',
                gcode_footer = 'This is test machine specific footer',
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
        assertMachinesEqual(self, orig, copied)


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
        machine2 = models.Machine.objects.get(pk=machine1.pk)
        machine2.delete()
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


    def test_session_model(self):
        # create material
        material = models.Material.objects.create(owner=self.user)
        # create session
        session = models.Session(owner=self.user,
                                material=models.Material.objects.get(pk=material.pk),
                                settings=models.Settings.objects.create(),
                                machine=models.Machine.objects.get(pk=self.machine.pk))

        session._persistence = json.dumps(json.loads(BLANK_PERSISTENCE)['persistence'])
        session.init_settings()
        session.update_persistence()

        session.save()
        # reload instances from db
        material = models.Material.objects.get(pk=material.pk)
        session = models.Session.objects.get(pk=session.pk)

        # check if material is copied
        self.assertTrue(material != session.material)
        self.assertTrue(material.pk != session.material.pk)
        self.assertTrue(material.owner != session.material.owner)

        self.assertEqual(material.name, session.material.name)
        self.assertEqual(material.size_od, session.material.size_od)

        # check if machine is copied
        self.machine.refresh_from_db()
        self.assertCopiedMachine(self.machine, session.machine)

        # check if gcode header and footer fields are included
        persistence = json.loads(session._persistence)
        self.assertTrue('gcode_header' in persistence['machine'].keys())
        self.assertEqual(self.machine.gcode_header, persistence['machine']['gcode_header'])
        self.assertTrue('gcode_footer' in persistence['machine'].keys())
        self.assertEqual(self.machine.gcode_footer, persistence['machine']['gcode_footer'])
        # delete session
        session1 = models.Session.objects.get(pk=session.pk)
        session1.delete()
        # check if dependancies are deleted
        removed_instances = (session1,
                             session1.machine,
                             session1.material)

        for obj in removed_instances:
            instances = type(obj).objects.filter(pk=obj.pk)
            self.assertEqual(len(instances), 0, msg='{} was not deleted'.format(obj))
