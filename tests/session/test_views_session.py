from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from session import models
from unittest.mock import Mock, patch
import re
from .testing_helpers import BLANK_PERSISTENCE, EXECUTED_LAST_TEST, get_routine, get_test_info
import json
from html.parser import HTMLParser


REDIRECT_MATCHER = re.compile(r'((?:[/\w-])+)\??')


class SessionSessionTest(TestCase):
    @classmethod
    def setUpClass(self):
        self.user = get_user_model().objects.create_user(email='known_user@somewhere.com',
                                                         password='SomeSecretPassword')

        self.user.activate_account()

        self.mode = models.SessionMode.objects.create()

        self.material = models.Material.objects.create(owner=self.user)

        self.machine = models.Machine.objects.create(owner=self.user,
                                                     model='SessionSessionTest Machine',
                                                     extruder=models.Extruder.objects.create(
                                                         nozzle=models.Nozzle.objects.create(size_id=0.7)),
                                                     chamber=models.Chamber.objects.create(temperature_max=100),
                                                     printbed=models.Printbed.objects.create(temperature_max=90)
                                                     )

    @classmethod
    def tearDownClass(self):
        self.user.delete()

    def extract_from_html(self, html_bytes, tag_match, attr_match):
        html_data = str(html_bytes, 'utf-8')
        result = []
        open_tags = []
        class BoolClass(object):
            capture = False

        data_capture = BoolClass()


        def tag_open(tag, attrs):
            # skip img tags, since they can exist without closing tag
            open_tags.append((tag, attrs))
            if tag_match(tag) and attr_match(attrs):
                data_capture.capture = True
            if data_capture.capture:
                result.append([tag, attrs, None])

        def tag_close(tag):
            if len(open_tags) < 1:
                raise Exception('Closing tag after end of document "{}"'.format(tag))
            if open_tags[-1][0] == tag:
                t, attrs = open_tags.pop()
                if tag_match(tag) and attr_match(attrs):
                    data_capture.capture = False
            else:
                data_capture.capture = False


        def handle_data(data):
            if len(open_tags) < 1:
                return
            if data_capture.capture:
                result[-1][-1] = data

        def start_end(tag, attrs):
            tag_open(tag, attrs)
            tag_close(tag)

        parser = HTMLParser()
        parser.handle_starttag = tag_open
        parser.handle_endtag = tag_close
        parser.handle_data = handle_data
        parser.handle_startendtag = start_end

        parser.feed(html_data)
        return result


    def extract_links(self, html_bytes):
        link_data = self.extract_from_html(html_bytes,
                                          lambda x: x=='a',
                                          lambda x: True)

        result = []
        for tag, attrs, data in link_data:
            for attr, val in attrs:
                if attr == 'href':
                    result.append((data, val))
        return result

    def test_sessions_list(self):
        tst_url = reverse('session_manager')
        # create some sessions without owner
        sessions = []
        expected_links = []
        persistence = json.loads(BLANK_PERSISTENCE)['persistence']
        persistence['session']['previous_tests'] = []
        persistence = json.dumps(persistence)
        for s_name in 'some testing session instances'.split(' '):
            session = models.Session(mode=models.SessionMode.objects.get(pk=self.mode.pk),
                                     name=s_name,
                                     material=models.Material.objects.get(pk=self.material.pk),
                                     settings=models.Settings.objects.create(),
                                     machine=models.Machine.objects.get(pk=self.machine.pk))

            session._persistence = persistence
            session.init_settings()
            session.update_persistence()

            session.persistence["session"]["previous_tests"] = []

            session.save()
            expected_links.append((len(sessions),
                                   session.name,
                                   reverse('session_detail', kwargs=dict(pk=session.pk))))
            sessions.append(session)

        # log in as user
        self.assertTrue(self.client.login(email='known_user@somewhere.com', password='SomeSecretPassword'))
        # make sure they are not visible in list
        resp = self.client.get(tst_url)
        self.assertEqual(resp.status_code, 200)

        links = self.extract_links(resp.content)
        found_links = [x for x in expected_links if x[1:] in links]

        self.assertEqual(len(found_links), 0,
                         msg='{} should not be in view'.format(list(sessions[x[0]] for x in found_links)))

        # assign ownership
        for s in sessions:
            s.owner = self.user
            s.save()
        # make sure they are visible
        resp = self.client.get(tst_url)
        self.assertEqual(resp.status_code, 200)

        links = self.extract_links(resp.content)
        missing_links = [x for x in expected_links if x[1:] not in links]

        self.assertEqual(len(missing_links), 0,
                         msg='{} should be in view'.format(list(sessions[x[0]] for x in missing_links)))

        # delete sessions
        for s in sessions:
            s.delete()
        # make sure they are no longer visible
        resp = self.client.get(tst_url)
        self.assertEqual(resp.status_code, 200)

        links = self.extract_links(resp.content)
        found_links = [x for x in expected_links if x[1:] in links]

        self.assertEqual(len(found_links), 0,
                         msg='{} should not be in view'.format(list(sessions[x[0]] for x in found_links)))

    def test_overview_redirection(self):
        persistence = json.loads(BLANK_PERSISTENCE)['persistence']
        persistence['session']['previous_tests'] = json.loads(EXECUTED_LAST_TEST)
        persistence = json.dumps(persistence)
        session = models.Session(mode=models.SessionMode.objects.get(pk=self.mode.pk),
                                 name='redirection test',
                                 owner=self.user,
                                 material=models.Material.objects.get(pk=self.material.pk),
                                 settings=models.Settings.objects.create(),
                                 machine=models.Machine.objects.get(pk=self.machine.pk))

        session._persistence = persistence
        session.init_settings()
        session.update_persistence()

        session.save()

        # log in as user
        self.assertTrue(self.client.login(email='known_user@somewhere.com', password='SomeSecretPassword'))
        with patch('optimizer_api.ApiClient.get_routine', side_effect=get_routine):
            with patch('optimizer_api.ApiClient.get_test_info', side_effect=get_test_info):
                session.test_number = '10'
                session.save()

            session_link = reverse('session_detail', kwargs=dict(pk=session.pk))
            # test dashboard and sessions list contain session link
            for dest in ('dashboard', 'session_manager'):
                resp = self.client.get(reverse(dest))
                self.assertEqual(resp.status_code, 200)
                links = self.extract_links(resp.content)
                self.assertTrue((session.name, session_link) in links,
                                msg='Session detail link not found in ' + dest)

            overview_link = reverse('session_overview', kwargs=dict(pk=session.pk))
            # make session completed and test if user gets redirected to overview
            session.refresh_from_db()
            with patch('optimizer_api.ApiClient.get_test_info', side_effect=get_test_info):
                # we don't actually care about next test number, so this is ok
                with patch('session.models.Session.test_number_next', side_effect=lambda primary: session.test_number):
                    resp = self.client.post(session_link,
                                            {"validation": "[2,1]",
                                                "comments": "",
                                                "btnprimary": ""},
                                            follow=True)

            self.assertEqual(resp.status_code, 200)
            self.assertTrue(len(resp.redirect_chain) > 0)
            self.assertEqual(resp.template_name[0], 'session/session_overview.html')

            # test dashboard and sessions list contain overview link
            for dest in ('dashboard', 'session_manager'):
                resp = self.client.get(reverse(dest))
                self.assertEqual(resp.status_code, 200)
                links = self.extract_links(resp.content)
                self.assertTrue((session.name, overview_link) in links,
                                msg='Session overview link not found in ' + dest)

            # make sure session link still accessible
            resp = self.client.get(session_link)
            self.assertEqual(resp.status_code, 200)

            # revert to last test
            session.delete_previous_test('10')
            session.save()

            # dashboard and sessions list should again contain session link
            for dest in ('dashboard', 'session_manager'):
                resp = self.client.get(reverse(dest))
                self.assertEqual(resp.status_code, 200)
                links = self.extract_links(resp.content)
                self.assertTrue((session.name, session_link) in links,
                                msg='Session detail link not found in ' + dest)

    def test_session_creation_cache(self):
        def extract_data(b):
            def attr_match(attrs):
                for attr, val in attrs:
                    if attr == 'selected':
                        return True
                    if attr == 'checked':
                        return True
                    elif attr == 'name' and val == 'name':
                        return True
                    elif attr == 'name' and val == 'mode':
                        return True
                return False

            result = []
            for _, attrs, data in self.extract_from_html(b, lambda x: x in ('input', 'option'), attr_match):
                for a, v in attrs:
                    if a == 'value':
                        result.append((v, data))
                        break

            return result

        tst_url = reverse('new_session')
        patched_name = 'Some session'
        self.assertTrue(self.client.login(email='known_user@somewhere.com', password='SomeSecretPassword'))

        # load new session page
        resp = self.client.get(tst_url)
        self.assertEqual(resp.status_code, 200)
        # make sure defaults are selected
        name, mode, machine, material = extract_data(resp.content)

        #Probably space from template
        self.assertEqual(mode, ('3', '\n            Guided (Free Tests Only)\n        '))
        self.assertEqual(name, ('Untitled', ' '))
        self.assertEqual(material, ('', '---------'))
        self.assertEqual(machine, ('', '---------'))
        # pach session name
        resp = self.client.patch(tst_url, data=patched_name)
        self.assertEqual(resp.status_code, 204)
        # load new session page and check defaults
        resp = self.client.get(tst_url)
        self.assertEqual(resp.status_code, 200)
        name, mode, machine, material = extract_data(resp.content)
        #Probably space from template
        self.assertEqual(mode, ('3', '\n            Guided (Free Tests Only)\n        '))
        self.assertEqual(name, (patched_name, ' '))
        self.assertEqual(material, ('', '---------'))
        self.assertEqual(machine, ('', '---------'))
        # use create material link. Should redirect back
        resp = self.client.post(reverse('material_form'),
                                dict(name='Material name', size_od=1.25, next=tst_url),
                                follow=True)
        self.assertEqual(resp.status_code, 200)
        name, mode, machine, material = extract_data(resp.content)
        self.assertEqual(name, (patched_name, ' '))
        self.assertFalse(material == ('', '---------'))
        self.assertEqual(machine, ('', '---------'))

        # use create machine link
        machine_props = {
            "model": "New machine test model",
            "buildarea_maxdim1": "12",
            "buildarea_maxdim2": "11",
            "form": "elliptic",
            "gcode_header": ";this is header",
            "gcode_footer": ";this is footer",
            "homing_sequence": ";should home at this point",
            "offset_1": "0",
            "offset_2": "0",
            "extruder_type": "bowden",
            "extruder-tool": "T0",
            "extruder-temperature_max": "350",
            "extruder-part_cooling": "on",
            "nozzle-size_id": "0.4",
            "chamber-tool": "",
            "chamber-gcode_command": "M141+S$temp",
            "chamber-temperature_max": "80",
            "printbed-printbed_heatable": "on",
            "printbed-temperature_max": "124",
            "next": tst_url
            }
        resp = self.client.post(reverse('machine_form'), machine_props, follow=True)
        self.assertEqual(resp.status_code, 200)
        name, mode, machine, material = extract_data(resp.content)

        self.assertEqual(name, (patched_name, ' '))
        self.assertFalse(material == ('', '---------'))
        self.assertFalse(machine == ('', '---------'))

        # create new session and check defaults
        p = json.loads(BLANK_PERSISTENCE)['persistence']
        with patch('optimizer_api.ApiClient.get_template', return_value=p):
            resp = self.client.post(tst_url,
                                    dict(mode=mode[0],
                                         name=name[0],
                                         material=material[0],
                                         machine=machine[0],
                                         target='aesthetics'))
        self.assertEqual(resp.status_code, 302)

        # load new session page
        resp = self.client.get(tst_url)
        self.assertEqual(resp.status_code, 200)
        # cache should be cleared now
        name, mode, machine, material = extract_data(resp.content)

        self.assertEqual(mode, ('3', '\n            Guided (Free Tests Only)\n        '))
        self.assertEqual(name, ('Untitled', ' '))
        self.assertEqual(material, ('', '---------'))
        self.assertEqual(machine, ('', '---------'))
