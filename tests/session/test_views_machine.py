from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from session import models
from unittest.mock import Mock, patch
import re

class SessionMaterialViewsTest(TestCase):
    @classmethod
    def setUpClass(self):
        self.user = get_user_model().objects.create_user(email='known_user@somewhere.com',
                                 is_active=True,
                                 password='SomeSecretPassword')

    @classmethod
    def tearDownClass(self):
        self.user.delete()

    def test_machine_detail(self):
        # create machine
        initial_model = 'Machine detail test'
        changed_model = 'Machine model changed'
        machine = models.Machine.objects.create(model=initial_model,
                                                chamber=models.Chamber.objects.create(),
                                                printbed=models.Printbed.objects.create(),
                                                extruder=models.Extruder.objects.create(
                                                    nozzle=models.Nozzle.objects.create()))

        test_url = reverse('machine_detail', kwargs=dict(pk=machine.pk))
        self.assertTrue(self.client.login(email='known_user@somewhere.com', password='SomeSecretPassword'))

        machine_form_data = {
                "model": changed_model,
                "buildarea_maxdim1": "0",
                "buildarea_maxdim2": "0",
                "form": "cartesian",
                "extruder_type": "bowden",
                "extruder-tool": "T0",
                "extruder-temperature_max": "350",
                "extruder-part_cooling": "on",
                "nozzle-size_id": "0.4",
                "chamber-tool": "",
                "chamber-gcode_command": "M141+S$temp",
                "chamber-temperature_max": "80",
                "printbed-printbed_heatable": "on",
                "printbed-temperature_max": "120"
                }

        # try to access machine from other account
        resp = self.client.get(test_url)
        self.assertEqual(resp.status_code, 404)

        # try to edit machine fro other account
        resp = self.client.post(test_url, machine_form_data)
        self.assertEqual(resp.status_code, 404)

        # machine should not be changed
        machine.refresh_from_db()
        self.assertTrue(machine.owner is None)
        self.assertEqual(machine.model, initial_model)

        machine.owner = self.user
        machine.save()
        # access machine from own account
        resp = self.client.get(test_url)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(bytes(initial_model, 'utf-8') in resp.content)

        # edit machine from own account
        resp = self.client.post(test_url, machine_form_data, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(len(resp.redirect_chain) > 0)
        self.assertEqual(resp.redirect_chain[-1][0], reverse('machine_manager'))

        # machine should be changed
        machine.refresh_from_db()
        self.assertEqual(machine.model, changed_model)

        # new details should be accessible
        resp = self.client.get(test_url)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(bytes(changed_model, 'utf-8') in resp.content)

        machine.delete()
        # try to access deleted machine
        resp = self.client.get(test_url)
        self.assertEqual(resp.status_code, 404)

        # try to edit deleted machine
        resp = self.client.post(test_url, machine_form_data)
        self.assertEqual(resp.status_code, 404)

        machines = models.Machine.objects.filter(pk=machine.pk)
        self.assertTrue(len(machines) == 0)
