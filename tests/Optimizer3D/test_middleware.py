from django.contrib.auth import get_user_model
from django.test import TestCase, RequestFactory, override_settings
from django.utils import timezone
from django.urls import reverse
from datetime import timedelta
import pytz
from unittest.mock import patch, Mock
from Optimizer3D.middleware.GeoRestrictAccessMiddleware import GeoRestrictAccessMiddleware
from django.core.exceptions import MiddlewareNotUsed, PermissionDenied


class SubscriptionMiddlewareTest(TestCase):
    @classmethod
    def setUpClass(self):
        expiration = timezone.datetime(year=2020, day=31, month=3, tzinfo=pytz.utc)
        self.beta_expired = expiration < timezone.now()


    @classmethod
    def tearDownClass(self):
        pass

    def test_premium_expiration(self):
        user = get_user_model().objects.create_user(email='known_user@somewhere.com',
                                 is_active=True,
                                 plan='premium',
                                 password='SomeSecretPassword')


        self.assertTrue(self.client.login(email='known_user@somewhere.com', password='SomeSecretPassword'))
        tst_url = reverse('dashboard')
        self.client.get(tst_url)

        user.refresh_from_db()
        # By default, premium should already be expired
        # If beta hasn't expired yet, user should have a premium
        self.assertEqual(user.plan, 'basic' if self.beta_expired else 'premium')

        user.plan = 'premium'
        user.subscription_expiration = timezone.now()
        user.save()
        self.client.get(tst_url)
        user.refresh_from_db()

        # should expire, because request was called after expiration was assigned
        self.assertEqual(user.plan, 'basic')

        user.plan = 'premium'
        user.subscription_expiration = timezone.now() + timedelta(seconds=2)
        user.save()
        self.client.get(tst_url)
        user.refresh_from_db()

        # should not expire, since we have few extra seconds
        self.assertEqual(user.plan, 'premium')


    def test_premium_assignment(self):
        user = get_user_model().objects.create_user(email='known_user@somewhere.com',
                                 is_active=True,
                                 password='SomeSecretPassword')


        self.assertTrue(self.client.login(email='known_user@somewhere.com', password='SomeSecretPassword'))
        tst_url = reverse('dashboard')
        self.client.get(tst_url)

        user.refresh_from_db()
        # User should have basic subscription by default
        # If it is still before beta expiration, user should have premium
        self.assertEqual(user.plan, 'basic' if self.beta_expired else 'premium')

        user.subscription_expiration = timezone.now() + timedelta(seconds=2)
        user.save()
        self.client.get(tst_url)
        user.refresh_from_db()

        # premium should be assigned, since user has few extra seconds
        self.assertEqual(user.plan, 'premium')


    def test_beta_premium_expiration(self):
        expiration = timezone.datetime(year=2020, day=31, month=3, tzinfo=pytz.utc)

        user = get_user_model().objects.create_user(email='known_user@somewhere.com',
                                 is_active=True,
                                 password='SomeSecretPassword')

        tst_url = reverse('dashboard')

        pre_expiration = expiration - timedelta(seconds=2)
        with patch('django.utils.timezone.now', return_value=pre_expiration):
            self.assertTrue(self.client.login(email='known_user@somewhere.com', password='SomeSecretPassword'))
            self.client.get(tst_url)

        user.refresh_from_db()
        # User should have premium subscription if it's still beta
        self.assertEqual(user.plan, 'premium')

        post_expiration = expiration + timedelta(seconds=2)
        with patch('django.utils.timezone.now', return_value=post_expiration):
            self.client.get(tst_url)

        user.refresh_from_db()

        # premium should be assigned, since user has few extra seconds
        self.assertEqual(user.plan, 'basic')


def add_location(request):
    request.geolocation = {
            "ip": "5.182.84.0",
            "continent": "Europe",
            "county": {
                "code": "RU",
                "name": "Russian Federation"
                },
            "geo": {
                "latitude": 61.52401,
                "latitude_dec": "63.125186920166016",
                "longitude": 105.318756,
                "longitude_dec": "103.75398254394531",
                "max_latitude": 82.1673907,
                "max_longitude": -168.9778799,
                "min_latitude": 41.185353,
                "min_longitude": 19.6160999,
                "bounds": {
                    "northeast": {
                        "lat": 82.1673907,
                        "lng": -168.9778799
                        },
                    "southwest": {
                        "lat": 41.185353,
                        "lng": 19.6160999
                        }
                    }
                },
            "raw_data": {
                "continent": "Europe",
                "address_format": "{{recipient}}\n{{postalcode}} {{city}}\n{{street}}\n{{country}}",
                "alpha2": "RU",
                "alpha3": "RUS",
                "country_code": "7",
                "international_prefix": "810",
                "ioc": "RUS",
                "gec": "RS",
                "name": "Russian Federation",
                "national_destination_code_lengths": [ 3 ],
                "national_number_lengths": [ 10 ],
                "national_prefix": "8",
                "number": "643",
                "region": "Europe",
                "subregion": "Eastern Europe",
                "world_region": "EMEA",
                "un_locode": "RU",
                "nationality": "Russian",
                "postal_code": True,
                "unofficial_names": [
                    "Russia",
                    "Russland",
                    "Russie",
                    "Rusia",
                    "\u30ed\u30b7\u30a2\u9023\u90a6",
                    "Rusland",
                    "\u0420\u043e\u0441\u0441\u0438\u044f",
                    "\u0420\u0430\u0441\u0456\u044f"
                    ],
                "languages_official": [ "ru" ],
                "languages_spoken": [ "ru" ],
                "geo": {
                    "latitude": 61.52401,
                    "latitude_dec": "63.125186920166016",
                    "longitude": 105.318756,
                    "longitude_dec": "103.75398254394531",
                    "max_latitude": 82.1673907,
                    "max_longitude": -168.9778799,
                    "min_latitude": 41.185353,
                    "min_longitude": 19.6160999,
                    "bounds": {
                        "northeast": {
                            "lat": 82.1673907,
                            "lng": -168.9778799
                            },
                        "southwest": {
                            "lat": 41.185353,
                            "lng": 19.6160999
                            }
                        }
                    },
                "currency_code": "RUB",
                "start_of_week": "monday"
            }
        }


class SubscriptionMiddlewareTest(TestCase):
    def test_geo_restriction_disabled(self):
        overrides = dict(GEO_RESTRICTION_BLACKLIST=None,
                        GEO_RESTRICTION_DISABLED=True,
                        GEO_RESTRICTION_WHITELIST=None)

        with override_settings(**overrides):
            with self.assertRaises(MiddlewareNotUsed):
                mware = GeoRestrictAccessMiddleware()

        overrides = dict(GEO_RESTRICTION_BLACKLIST=[],
                        GEO_RESTRICTION_DISABLED=None,
                        GEO_RESTRICTION_WHITELIST=[])

        with override_settings(**overrides):
            mware = GeoRestrictAccessMiddleware()


    def test_geo_restriction(self):
        factory = RequestFactory()
        pathing_path = 'django_ip_geolocation.middleware.IpGeolocationMiddleware.process_request'

        req = factory.get('/')
        location_mock = Mock(side_effect=add_location)

        # test passing blacklist
        overrides = dict(GEO_RESTRICTION_BLACKLIST=['US', 'LV', 'GB'],
                        GEO_RESTRICTION_DISABLED=None,
                        GEO_RESTRICTION_WHITELIST=None)

        with override_settings(**overrides):
            mware = GeoRestrictAccessMiddleware()
            with patch(pathing_path, location_mock):
                mware.process_request(req)

        location_mock.assert_called_once()

        # test blacklisting
        overrides['GEO_RESTRICTION_BLACKLIST'].append('RU')
        location_mock.reset_mock()

        with override_settings(**overrides):
            with patch(pathing_path, location_mock):
                with self.assertRaises(PermissionDenied):
                    mware.process_request(req)
                    mware.process_view(req, None, None, None)

        location_mock.assert_called_once()

        # test restriction by whitelist
        location_mock.reset_mock()
        overrides = dict(GEO_RESTRICTION_WHITELIST=['US', 'LV', 'GB'],
                        GEO_RESTRICTION_DISABLED=None,
                        GEO_RESTRICTION_BLACKLIST=None)

        with override_settings(**overrides):
            mware = GeoRestrictAccessMiddleware()
            with patch(pathing_path, location_mock):
                with self.assertRaises(PermissionDenied):
                    mware.process_request(req)
                    mware.process_view(req, None, None, None)

        location_mock.assert_called_once()

        # test whitelisting
        overrides['GEO_RESTRICTION_WHITELIST'].append('RU')
        location_mock.reset_mock()

        with override_settings(**overrides):
            with patch(pathing_path, location_mock):
                mware.process_request(req)

        location_mock.assert_called_once()

        # Test prefer whitelist over blacklist
        overrides = dict(GEO_RESTRICTION_BLACKLIST=['RU'],
                        GEO_RESTRICTION_WHITELIST=['RU'])
        location_mock.reset_mock()

        with override_settings(**overrides):
            with patch(pathing_path, location_mock):
                mware.process_request(req)

