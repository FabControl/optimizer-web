from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from session import models
from session import urls
from unittest.mock import Mock, patch
import re
from .testing_helpers import BLANK_PERSISTENCE
from django.conf import settings


REDIRECT_MATCHER = re.compile(r'((?:[/\w-])+)\??')

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

        self.assertTrue(bytes("location.href='{}'".format(reverse('new_session')), 'utf-8')
                        in resp.content)


    def test_login_required(self):
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
        test_session = models.Session.objects.create(owner=self.user,
                                          name='some',
                                          machine=machine,
                                          material=material,
                                          _persistence='{"session":{"previous_tests":[]}}',
                                          settings=sett)

        sample_owner = get_user_model().objects.get(email=settings.SAMPLE_SESSIONS_OWNER)
        sample_machine = models.Machine.objects.filter(owner=sample_owner)[0]

        staff_only_urls = [
                ('session_json', {'pk': test_session.pk}),
                ('session__test_info', {'pk': test_session.pk})
                ]
        # order does matter
        login_req_urls = [
                ('dashboard', {}),
                ('material_manager', {}),
                ('material_form', {}),
                ('material_detail', {'pk': material.pk}),
                ('material_delete', {'pk': material.pk}),
                ('machine_manager', {}),
                ('machine_form', {}),
                ('machine_detail', {'pk': machine.pk}),
                ('machine_sample', {'pk': sample_machine.pk}),
                ('machine_delete', {'pk': machine.pk}),
                ("session_manager", {}),
                ('session_detail', {'pk': test_session.pk}),
                ('session_validate_back', {'pk': test_session.pk}),
                ('revert_to_test', {'pk': test_session.pk}),
                ('session_next_test', {'pk': test_session.pk, 'priority': 'priority'}),
                ('gcode', {'pk': test_session.pk}),
                ('config', {'pk': test_session.pk, 'slicer': 'slicer'}),
                ('report', {'pk': test_session.pk}),
                ('session_delete', {'pk': test_session.pk}),
                ('session_overview', {'pk': test_session.pk}),
                ('test_switch', {'pk': test_session.pk, 'number': '5'}),
                ('new_session', {}),
                ("faq", {}),
                ("quickstart", {}),
                ("support", {}),
                ('testing_session', {}),
                ('privacy_statement', {}),
                ('investor_dashboard', {})
                ]

        no_login_urls = [
                ("terms_of_use", {}),
                ("health_check", {})
                ]

        # we do not check index, since it redirects to dashboard
        self.assertEqual(len(login_req_urls) + len(no_login_urls) + len(staff_only_urls),
                         len(urls.urlpatterns) - 1,
                         msg='Have You added/removed some views and forgot about tests?')

        self.client.logout()

        class MockedBackendResponse():
            def __init__(s):
                s.status_code = 200
                s.text = BLANK_PERSISTENCE

        with patch('requests.post', return_value=MockedBackendResponse()):
            # should be accessible without login
            for url_name, kwargs in no_login_urls:
                resp = self.client.get(reverse(url_name, kwargs=kwargs))
                self.assertEqual(resp.status_code, 200, msg='Url name: {}'.format(url_name))

        login_url = reverse('login')
        # Login required for these views
        for url_name, kwargs in (login_req_urls + staff_only_urls):
            resp = self.client.get(reverse(url_name, kwargs=kwargs), follow=True)
            self.assertEqual(resp.status_code, 200, msg='Url name: {}'.format(url_name))
            self.assertTrue((len(resp.redirect_chain) > 0), msg='Url name: {}'.format(url_name))

            r = REDIRECT_MATCHER.match(resp.redirect_chain[-1][0])
            self.assertTrue((r is not None), msg='Url name: {}'.format(url_name))
            self.assertEqual(r.group(1), login_url, msg='Url name: {}'.format(url_name))



        self.assertTrue(self.client.login(email='known_user@somewhere.com', password='SomeSecretPassword'))
        # These urls are staff only, otherwise 404
        for url_name, kwargs in staff_only_urls:
            resp = self.client.get(reverse(url_name, kwargs=kwargs), follow=True)
            self.assertEqual(resp.status_code, 404, msg='Url name: {}'.format(url_name))

        self.user.is_staff = True
        self.user.save()

        with patch('requests.post', return_value=MockedBackendResponse()):
            for url_name, kwargs in staff_only_urls:
                resp = self.client.get(reverse(url_name, kwargs=kwargs), follow=True)
                self.assertEqual(resp.status_code, 200, msg='Url name: {}'.format(url_name))

        self.user.is_staff = False
        self.user.save()

    def test_terms_of_use(self):
        tst_url = reverse('terms_of_use')
        self.client.logout()
        resp = self.client.get(tst_url)

        self.assertEqual(resp.status_code, 200)
