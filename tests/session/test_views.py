from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from session import models
from session import urls
from unittest.mock import Mock, patch
import re

BLANK_PERSISTENCE = """
{
    "persistence": {
        "machine": {
            "model": "Mass Portal XD20",
            "buildarea_maxdim1": 200,
            "buildarea_maxdim2": 200,
            "form": "elliptic",
            "temperature_controllers": {
                "extruder": {
                    "tool": "T0",
                    "temperature_max": 350,
                    "part_cooling": true,
                    "nozzle": {
                        "size_id": 0.8
                    }
                },
                "chamber": {
                    "tool": "",
                    "gcode_command": "M141 S$temp",
                    "temperature_max": 80,
                    "chamber_heatable": false
                },
                "printbed": {
                    "printbed_heatable": true
                }
            }
        },
        "material": {
            "size_od": 1.75,
            "name": "FormFutura Premium M"
        },
        "session": {
            "uid": 95,
            "target": "mechanical_strength",
            "test_number": "10",
            "min_max_parameter_one": [],
            "min_max_parameter_two": [
                10.0,
                30.0
            ],
            "min_max_parameter_three": [
                60.0,
                120.0
            ],
            "test_type": "A",
            "user_id": "user name",
            "offset": [
                0,
                0
            ],
            "slicer": "Prusa",
            "previous_tests": [
                {
                    "comments": 0,
                    "datetime_info": "2019-11-13 14:13:04",
                    "executed": true,
                    "extruded_filament_mm": 1183.18,
                    "parameter_one_name": "first-layer track height",
                    "parameter_one_precision": "{:.2f}",
                    "parameter_one_units": "mm",
                    "parameter_three_name": null,
                    "parameter_two_name": "first-layer printing speed",
                    "parameter_two_precision": "{:.0f}",
                    "parameter_two_units": "mm/s",
                    "selected_parameter_one_value": 0.33,
                    "selected_parameter_two_value": 17.0,
                    "selected_volumetric_flow-rate_value": 0,
                    "test_name": "first-layer track height vs first-layer printing speed",
                    "test_number": "01",
                    "tested_parameter_one_values": [
                        0.22,
                        0.26,
                        0.29,
                        0.33,
                        0.37,
                        0.4,
                        0.44
                    ],
                    "tested_parameter_two_values": [
                        10.0,
                        17.0,
                        23.0,
                        30.0
                    ],
                    "tested_parameters": [
                        {
                            "active": true,
                            "hint_active": null,
                            "min_max": [
                                0.08000000000000002,
                                0.8
                            ],
                            "name": "first-layer track height",
                            "precision": "{:.2f}",
                            "programmatic_name": "track_height_raft",
                            "units": "mm",
                            "values": [
                                0.22,
                                0.25666666666666665,
                                0.29333333333333333,
                                0.33,
                                0.3666666666666667,
                                0.4033333333333333,
                                0.44
                            ]
                        },
                        {
                            "active": true,
                            "hint_active": "Typically, the values in the range of 5-15 mm/s are adequate for printing flexible materials; for harder materials, you can go up to 10-30 mm/s.",
                            "min_max": [
                                1,
                                140
                            ],
                            "name": "first-layer printing speed",
                            "precision": "{:.0f}",
                            "programmatic_name": "speed_printing_raft",
                            "units": "mm/s",
                            "values": [
                                10.0,
                                16.666666666666668,
                                23.333333333333336,
                                30.0
                            ]
                        }
                    ],
                    "tested_volumetric_flow-rate_values": [
                        [
                            1.656,
                            1.912,
                            2.162,
                            2.406,
                            2.645,
                            2.878,
                            3.105
                        ],
                        [
                            2.76,
                            3.187,
                            3.603,
                            4.01,
                            4.408,
                            4.796,
                            5.174
                        ],
                        [
                            3.864,
                            4.461,
                            5.045,
                            5.615,
                            6.171,
                            6.714,
                            7.244
                        ],
                        [
                            4.968,
                            5.736,
                            6.486,
                            7.219,
                            7.934,
                            8.633,
                            9.314
                        ]
                    ],
                    "validated": true
                },
                {
                    "comments": 0,
                    "datetime_info": "2019-11-15 09:59:11",
                    "executed": true,
                    "extruded_filament_mm": 3943.753,
                    "parameter_one_name": "extrusion temperature",
                    "parameter_one_precision": "{:.0f}",
                    "parameter_one_units": "degC",
                    "parameter_three_name": null,
                    "parameter_two_name": "printing speed",
                    "parameter_two_precision": "{:.0f}",
                    "parameter_two_units": "mm/s",
                    "selected_parameter_one_value": 272.0,
                    "selected_parameter_two_value": 23.0,
                    "selected_volumetric_flow-rate_value": 0,
                    "test_name": "extrusion temperature vs printing speed",
                    "test_number": "03",
                    "tested_parameter_one_values": [
                        260.0,
                        266.0,
                        272.0,
                        278.0,
                        285.0,
                        291.0,
                        297.0
                    ],
                    "tested_parameter_two_values": [
                        10.0,
                        17.0,
                        23.0,
                        30.0
                    ],
                    "tested_parameters": [
                        {
                            "active": true,
                            "hint_active": null,
                            "min_max": [
                                30,
                                350
                            ],
                            "name": "extrusion temperature",
                            "precision": "{:.0f}",
                            "programmatic_name": "temperature_extruder",
                            "units": "degC",
                            "values": [
                                260.0,
                                266.0,
                                272.0,
                                278.0,
                                285.0,
                                291.0,
                                297.0
                            ]
                        },
                        {
                            "active": true,
                            "hint_active": null,
                            "min_max": [
                                1,
                                140
                            ],
                            "name": "printing speed",
                            "precision": "{:.0f}",
                            "programmatic_name": "speed_printing",
                            "units": "mm/s",
                            "values": [
                                10.0,
                                16.666666666666668,
                                23.333333333333336,
                                30.0
                            ]
                        }
                    ],
                    "tested_volumetric_flow-rate_values": [
                        [
                            1.514,
                            1.514,
                            1.514,
                            1.514,
                            1.514,
                            1.514,
                            1.514
                        ],
                        [
                            2.524,
                            2.524,
                            2.524,
                            2.524,
                            2.524,
                            2.524,
                            2.524
                        ],
                        [
                            3.533,
                            3.533,
                            3.533,
                            3.533,
                            3.533,
                            3.533,
                            3.533
                        ],
                        [
                            4.542,
                            4.542,
                            4.542,
                            4.542,
                            4.542,
                            4.542,
                            4.542
                        ]
                    ],
                    "validated": true
                },
                {
                    "comments": 0,
                    "datetime_info": "2019-11-15 09:59:23",
                    "executed": true,
                    "extruded_filament_mm": 3153.209,
                    "parameter_one_name": "extrusion temperature",
                    "parameter_one_precision": "{:.0f}",
                    "parameter_one_units": "degC",
                    "parameter_three_name": "retraction speed",
                    "parameter_three_precision": "{:.0f}",
                    "parameter_three_units": "mm/s",
                    "parameter_two_name": "retraction distance",
                    "parameter_two_precision": "{:.3f}",
                    "parameter_two_units": "mm",
                    "selected_parameter_one_value": 0,
                    "selected_parameter_three_value": 0,
                    "selected_parameter_two_value": 0,
                    "selected_volumetric_flow-rate_value": 3.483,
                    "test_name": "extrusion temperature vs retraction distance",
                    "test_number": "08",
                    "tested_parameter_one_values": [
                        267.0,
                        269.0,
                        270.0,
                        272.0,
                        274.0,
                        275.0,
                        277.0
                    ],
                    "tested_parameter_three_values": [
                        60.0,
                        120.0
                    ],
                    "tested_parameter_two_values": [
                        0.0,
                        1.333,
                        2.667,
                        4.0
                    ],
                    "tested_parameters": [
                        {
                            "active": true,
                            "hint_active": null,
                            "min_max": [
                                30,
                                350
                            ],
                            "name": "extrusion temperature",
                            "precision": "{:.0f}",
                            "programmatic_name": "temperature_extruder",
                            "units": "degC",
                            "values": [
                                267.0,
                                268.6666666666667,
                                270.3333333333333,
                                272.0,
                                273.6666666666667,
                                275.3333333333333,
                                277.0
                            ]
                        },
                        {
                            "active": true,
                            "hint_active": null,
                            "min_max": [
                                0,
                                20
                            ],
                            "name": "retraction distance",
                            "precision": "{:.3f}",
                            "programmatic_name": "retraction_distance",
                            "units": "mm",
                            "values": [
                                0.0,
                                1.3333333333333333,
                                2.6666666666666665,
                                4.0
                            ]
                        },
                        {
                            "active": true,
                            "hint_active": null,
                            "min_max": [
                                1,
                                140
                            ],
                            "name": "retraction speed",
                            "precision": "{:.0f}",
                            "programmatic_name": "retraction_speed",
                            "units": "mm/s",
                            "values": [
                                60.0,
                                120.0
                            ]
                        }
                    ],
                    "tested_volumetric_flow-rate_values": [
                        3.483
                    ],
                    "validated": false
                }
            ]
        },
        "settings": {
            "speed_travel": 140,
            "raft_density": 100,
            "speed_printing_raft": 17,
            "track_height": 0.2,
            "track_height_raft": 0.33,
            "track_width": 0.8,
            "track_width_raft": 0.8,
            "extrusion_multiplier": 1.0,
            "temperature_extruder": 272,
            "temperature_extruder_raft": 260,
            "retraction_restart_distance": 0.0,
            "retraction_speed": 100,
            "retraction_distance": 0.0,
            "bridging_extrusion_multiplier": 1.0,
            "bridging_part_cooling": 0,
            "bridging_speed_printing": 0,
            "speed_printing": 23,
            "coasting_distance": 0.0,
            "critical_overhang_angle": 27,
            "temperature_printbed_setpoint": 90,
            "temperature_chamber_setpoint": 0,
            "part_cooling_setpoint": 0
        }
    }
}
"""

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
                ('testing_session', {})
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

