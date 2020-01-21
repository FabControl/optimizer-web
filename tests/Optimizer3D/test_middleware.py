from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from django.urls import reverse
from datetime import timedelta
import pytz


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

