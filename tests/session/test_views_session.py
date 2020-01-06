from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from session import models
from unittest.mock import Mock, patch
import re
from .testing_helpers import BLANK_PERSISTENCE
import json
from html.parser import HTMLParser


REDIRECT_MATCHER = re.compile(r'((?:[/\w-])+)\??')

class SessionSessionTest(TestCase):
    @classmethod
    def setUpClass(self):
        self.user = get_user_model().objects.create_user(email='known_user@somewhere.com',
                                 is_active=True,
                                 password='SomeSecretPassword')

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

    def extract_links(self, html_bytes):
        html_data = str(html_bytes, 'utf-8')
        result = []
        open_tags = []

        def tag_open(tag, attrs):
            # skip img tags, since they can exist without closing tag
            if tag in ('link', 'meta', 'img', 'input'):
                return
            open_tags.append((tag, attrs))

        def tag_close(tag):
            if len(open_tags) < 1:
                raise Exception('Closing tag after end of document "{}"'.format(tag))
            self.assertEqual(open_tags[-1][0], tag)
            open_tags.pop()

        def handle_data(data):
            if len(open_tags) < 1:
                return
            if open_tags[-1][0] == 'a':
                for (attr, val) in open_tags[-1][1]:
                    if attr == 'href':
                        result.append((data, val))
                        break

        def start_end(tag, attrs): pass

        parser = HTMLParser()
        parser.handle_starttag = tag_open
        parser.handle_endtag = tag_close
        parser.handle_data = handle_data
        parser.handle_startendtag = start_end

        parser.feed(html_data)
        return result


    def test_sessions_list(self):
        tst_url = reverse('session_manager')
        # create some sessions without owner
        sessions = []
        expected_links = []
        for s_name in 'some testing session instances'.split(' '):
            session = models.Session(name=s_name,
                                    material=models.Material.objects.get(pk=self.material.pk),
                                    settings=models.Settings.objects.create(),
                                    machine=models.Machine.objects.get(pk=self.machine.pk))

            session._persistence = json.dumps(json.loads(BLANK_PERSISTENCE)['persistence'])
            session.init_settings()
            session.update_persistence()

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
