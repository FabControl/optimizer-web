from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from session import models
from unittest.mock import Mock, patch
import re
from django.conf import settings
from .testing_helpers import assertMachinesEqual

class SessionMachineViewsTest(TestCase):
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

    def test_machines_view(self):
        name = 'Machines view test machine'
        size = 0.5

        machine = models.Machine.objects.create(model=name,
                                                chamber=models.Chamber.objects.create(),
                                                printbed=models.Printbed.objects.create(),
                                                extruder=models.Extruder.objects.create(
                                                    nozzle=models.Nozzle.objects.create(size_id=size)))

        details_url = reverse('machine_detail', kwargs={'pk': machine.pk})
        delete_url = reverse('machine_delete', kwargs={'pk': machine.pk})

        # Should not show machines from other users
        tst_url = reverse('machine_manager')

        self.assertTrue(self.client.login(email='known_user@somewhere.com', password='SomeSecretPassword'))

        resp = self.client.get(tst_url)

        self.assertEqual(200, resp.status_code)
        self.assertFalse(bytes(name, 'utf-8') in resp.content)
        self.assertFalse(bytes(str(size), 'utf-8') in resp.content)
        self.assertFalse(bytes(details_url, 'utf-8') in resp.content)
        self.assertFalse(bytes(delete_url, 'utf-8') in resp.content)

        # should show machines from current user
        machine.owner = self.user
        machine.save()

        resp = self.client.get(tst_url)

        self.assertEqual(200, resp.status_code)
        self.assertTrue(bytes(name, 'utf-8') in resp.content)
        self.assertTrue(bytes(str(size), 'utf-8') in resp.content)
        self.assertTrue(bytes(details_url, 'utf-8') in resp.content)
        self.assertTrue(bytes(delete_url, 'utf-8') in resp.content)

        # should not show machine after deletion
        machine.delete()

        resp = self.client.get(tst_url)

        self.assertEqual(200, resp.status_code)
        self.assertFalse(bytes(name, 'utf-8') in resp.content)
        self.assertFalse(bytes(str(size), 'utf-8') in resp.content)
        self.assertFalse(bytes(details_url, 'utf-8') in resp.content)
        self.assertFalse(bytes(delete_url, 'utf-8') in resp.content)

    def test_new_machine_creation(self):
        direct_props = {
            "model": "New machine test model",
            "buildarea_maxdim1": "12",
            "buildarea_maxdim2": "11",
            "form": "elliptic"
            }

        subprops = {
            "extruder_type": "bowden",
            "extruder-tool": "T0",
            "extruder-temperature_max": "350",
            "extruder-part_cooling": "on",
            "nozzle-size_id": "0.4",
            "chamber-tool": "",
            "chamber-gcode_command": "M141+S$temp",
            "chamber-temperature_max": "80",
            "printbed-printbed_heatable": "on",
            "printbed-temperature_max": "124"
            }

        tst_url = reverse('machine_form')

        self.assertTrue(self.client.login(email='known_user@somewhere.com', password='SomeSecretPassword'))

        # creation form should be accessible
        resp = self.client.get(tst_url)
        self.assertEqual(200, resp.status_code)

        # make sure machine does not exist
        machines = models.Machine.objects.filter(**direct_props)
        self.assertEqual(len(machines), 0,
                         msg='Can not perform test, because machine already exists')
        # post data
        d = {}
        d.update(direct_props)
        d.update(subprops)
        resp = self.client.post(tst_url, d, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(len(resp.redirect_chain) > 0)
        self.assertEqual(resp.redirect_chain[-1][0], reverse('machine_manager'))

        # check if machine was created
        machine = models.Machine.objects.get(**direct_props)
        self.assertEqual(machine.owner, self.user)

    def test_machine_deletion(self):
        # create machine
        machine = models.Machine.objects.create(chamber=models.Chamber.objects.create(),
                                                printbed=models.Printbed.objects.create(),
                                                extruder=models.Extruder.objects.create(
                                                    nozzle=models.Nozzle.objects.create()))

        delete_url = reverse('machine_delete', kwargs={'pk': machine.pk})

        self.assertTrue(self.client.login(email='known_user@somewhere.com', password='SomeSecretPassword'))

        # check with other user's machine
        resp = self.client.get(delete_url)
        self.assertEqual(resp.status_code, 404)
        # machine should still be in db
        machines = models.Machine.objects.filter(pk=machine.pk, owner=None)
        self.assertEqual(len(machines), 1)

        resp = self.client.post(delete_url)
        self.assertEqual(resp.status_code, 404)
        # machine should still be in db
        machines = models.Machine.objects.filter(pk=machine.pk, owner=None)
        self.assertEqual(len(machines), 1)

        # check with owned machine
        machine.owner = self.user
        machine.save()

        resp = self.client.get(delete_url)
        self.assertEqual(resp.status_code, 404)
        # machine should still be in db
        machines = models.Machine.objects.filter(pk=machine.pk, owner=self.user)
        self.assertEqual(len(machines), 1)

        # successful delete redirects to machines list
        resp = self.client.post(delete_url, follow=True)
        self.assertEqual(resp.status_code, 200)

        self.assertTrue(len(resp.redirect_chain) > 0)
        self.assertEqual(resp.redirect_chain[-1][0], reverse('machine_manager'))

        # machine should be removed
        machines = models.Machine.objects.filter(pk=machine.pk)
        self.assertEqual(len(machines), 0)

        # check with non-existing machine
        resp = self.client.get(delete_url)
        self.assertEqual(resp.status_code, 404)
        # machine should not exist
        machines = models.Machine.objects.filter(pk=machine.pk)
        self.assertEqual(len(machines), 0)

        resp = self.client.post(delete_url)
        self.assertEqual(resp.status_code, 404)
        # machine should not exist
        machines = models.Machine.objects.filter(pk=machine.pk)
        self.assertEqual(len(machines), 0)

    def test_sample_machine_data(self):
        owner = get_user_model().objects.get(email=settings.SAMPLE_SESSIONS_OWNER)
        sample_machine = models.Machine.objects.filter(owner=owner)[0]

        machines_filter = dict(owner=self.user,
                               model=sample_machine.model,
                               buildarea_maxdim1=sample_machine.buildarea_maxdim1,
                               buildarea_maxdim2=sample_machine.buildarea_maxdim2,
                               form=sample_machine.form,
                               extruder_type=sample_machine.extruder_type,
                               )
        existing_machines = models.Machine.objects.filter(**machines_filter)
        self.assertEqual(len(existing_machines), 0, msg='User already has similar machine - change sample_machine')

        self.assertTrue(self.client.login(email='known_user@somewhere.com', password='SomeSecretPassword'))


        # check if valid json is returned
        resp = self.client.get(reverse('machine_sample', args=(sample_machine.pk,)))
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json() is not None)

        # check if posting received data creates new machine
        resp = self.client.post(reverse('machine_form'), resp.json())
        created_machines = models.Machine.objects.filter(**machines_filter)

        self.assertEqual(len(created_machines), 1)

        created = created_machines[0]

        self.assertEqual(created.owner, self.user)
        self.assertEqual(sample_machine.owner, owner)
        assertMachinesEqual(self, created, sample_machine)

        # only specific user's machines should be accessible
        resp = self.client.get(reverse('machine_sample', args=(created.pk,)))
        self.assertEqual(resp.status_code, 404)
