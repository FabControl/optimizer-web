from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from session import models


class SessionViewsTest(TestCase):
    @classmethod
    def setUpClass(self):
        self.user = get_user_model().objects.create_user(email='known_user@somewhere.com',
                                 is_active=True,
                                 password='SomeSecretPassword')

    @classmethod
    def tearDownClass(self):
        self.user.delete()

    def test_index_page(self):
        self.client.logout()
        resp = self.client.get('', follow=True)
        # logged out sessions redirect to login page
        self.assertTrue(len(resp.redirect_chain) > 0)
        self.assertFalse(resp.redirect_chain[-1][0] == reverse('dashboard'))

        self.assertTrue(self.client.login(email='known_user@somewhere.com', password='SomeSecretPassword'))

        resp = self.client.get('', follow=True)
        # dashboard should be used as index page
        self.assertTrue(len(resp.redirect_chain) > 0)
        self.assertTrue(resp.redirect_chain[-1][0] == reverse('dashboard'))

    def test_dashboard(self):
        test_sessions = 'Test one;Test two;Test three;Test four;Test five'.split(';')
        test_url = reverse('dashboard')

        self.assertTrue(self.client.login(email='known_user@somewhere.com', password='SomeSecretPassword'))

        resp = self.client.get(test_url)
        for s in test_sessions:
            self.assertFalse(bytes(s, 'utf-8') in resp.content)

        nozzle = models.Nozzle.objects.create()
        extruder = models.Extruder.objects.create(nozzle=nozzle)
        chamber = models.Chamber.objects.create()
        printbed = models.Printbed.objects.create()
        machine = models.Machine.objects.create(owner=self.user, extruder=extruder,
                                                chamber=chamber, printbed=printbed)

        material = models.Material(owner=self.user, name='material')
        material.save()

        sett = models.Settings()
        sett.save()
        # create testing sessions
        for s in test_sessions:
            models.Session.objects.create(owner=self.user,
                                          name=s,
                                          machine=machine,
                                          material=material,
                                          _persistence='{"session":{"previous_tests":[]}}',
                                          settings=sett)

        # check if new sessions are visible in dashboard
        resp = self.client.get(test_url)
        for s in test_sessions:
            self.assertTrue(bytes(s, 'utf-8') in resp.content)

