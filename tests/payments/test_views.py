from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.conf import settings
from django.utils import timezone
from uuid import uuid4
import json
import stripe
from unittest.mock import Mock, patch
from payments.models import Plan, Checkout
from datetime import timedelta


# helper class
class CheckoutTestItem:
    def __init__(self, cancel_url, success_url, line_items, client_reference_id):
        self.cancel_url=cancel_url
        self.success_url=success_url
        self.total_amount = sum(x['amount'] for x in line_items)
        self.checkout_id = client_reference_id
        self.stripe_id = 'stripe' + str(uuid4())

class PaymentPlansViewTest(TestCase):
    @classmethod
    def setUpClass(self):
        self.test_url = reverse('plans')
        self.user = get_user_model().objects.create_user(email='known_user@somewhere.com',
                                is_active=True,
                                password='SomeSecretPassword')
        self.plans = [
                Plan(name='Core'),
                Plan(name='Day', price=5, type='premium', subscription_period=timedelta(days=1)),
                Plan(name='Week', price=25, type='premium', subscription_period=timedelta(days=7)),
                Plan(name='Month', price=75, type='premium', subscription_period=timedelta(days=31))
                ]
        for p in self.plans:
            p.save()

    @classmethod
    def tearDownClass(self):
        self.user.delete()
        for p in self.plans:
            p.delete()

    @classmethod
    def setUp(self):
        self.checkouts = []
        self.webhooks = []

    # imitates stripe.Checkout.create method
    # documentation https://stripe.com/docs/api/checkout/sessions/create
    def checkout_dummy(self, cancel_url=None,
                        payment_method_types=None,
                        success_url=None,
                        billing_address_collection=None,
                        client_reference_id=None,
                        customer=None,
                        customer_email=None,
                        line_items=None,
                        locale=None,
                        mode=None,
                        payment_intent_data=None,
                        setup_intent_data=None,
                        submit_type=None,
                        subscription_data=None):

        # Stripe api key should be set before calling Checkout.create()
        self.assertEqual(stripe.api_key, settings.STRIPE_API_KEY)
        # required kwargs
        self.assertFalse(cancel_url is None)
        self.assertEqual(payment_method_types, ['card'])
        self.assertFalse(success_url is None)
        self.assertTrue(isinstance(line_items, list))
        self.assertEqual(len(line_items), 1)

        for i in line_items:
            keys = i.keys()
            for k in ['amount', 'currency', 'name', 'quantity']:
                self.assertTrue(k in keys, msg='"{0}" not in {1}'.format(k, i))

        test_item = CheckoutTestItem(cancel_url, success_url,
                                     line_items, client_reference_id)
        test_item.session_value = {
                'id': test_item.stripe_id,
                'object': 'checkout.session',
                'billing_address_collection': billing_address_collection,
                'cancel_url': cancel_url,
                'client_reference_id': str(client_reference_id),
                'customer': customer,
                'customer_email': customer_email,
                'display_items': line_items,
                'livemode': False,
                'locale': locale,
                'mode': mode,
                'payment_intent': test_item.stripe_id,
                'payment_method_types': payment_method_types,
                'setup_intent': setup_intent_data,
                'submit_type': submit_type,
                'subscription': subscription_data,
                'success_url': success_url,
                'line_items': line_items
                }

        self.checkouts.append(test_item)

        return test_item.session_value

    def test_payment_workflow(self):
        self.assertTrue(self.client.login(email='known_user@somewhere.com',
                                          password='SomeSecretPassword'))

        self.user.refresh_from_db()
        current_expiration = self.user.subscription_expiration
        plan = self.plans[2]
        result_timestamp_min = max(current_expiration, timezone.now()) + plan.subscription_period

        # ask for premium plan extension
        checkout_mock = Mock(side_effect=self.checkout_dummy)
        with patch('stripe.checkout.Session.create', checkout_mock):
            resp = self.client.post(self.test_url, {'plan_id':plan.pk},
                                    HTTP_HOST=settings.ALLOWED_HOSTS[0])

        self.assertEqual(resp.status_code, 200)
        self.assertTrue('payments/checkout.html' in (x.name for x in resp.templates))

        # user's current subscription should not be changed yet
        self.user.refresh_from_db()
        self.assertEqual(self.user.subscription_expiration, current_expiration)

        # notify server about checkout completion
        webhook_mock = Mock(return_value={'data' : {
                                            'object' : self.checkouts[-1].session_value},
                                          'type' : 'checkout.session.completed'})
        with patch('stripe.Webhook.construct_event', webhook_mock):
            c = Client(HTTP_STRIPE_SIGNATURE='checkout complete')
            resp = c.post(reverse('confirm_payment'), {'data': ''})
        self.assertEqual(resp.status_code, 200)

        # check subscription expiration time
        self.user.refresh_from_db()
        result_timestamp_max = max(current_expiration, timezone.now()) + plan.subscription_period

        self.assertTrue(self.user.subscription_expiration >= result_timestamp_min)
        self.assertTrue(self.user.subscription_expiration <= result_timestamp_max)

    def test_webhook_validation(self):
        test_url = reverse('confirm_payment')
        self.user.refresh_from_db()
        expiration_base = self.user.subscription_expiration
        # create checkout object
        checkout = Checkout(user=self.user,
                            stripe_id=uuid4(),
                            payment_plan=self.plans[2])

        checkout.save()
        # make sure header is required
        resp = self.client.post(test_url, {'data':''})
        self.assertEqual(resp.status_code, 400)
        self.user.refresh_from_db()
        self.assertEqual(self.user.subscription_expiration, expiration_base)

        # make sure errors are handled properly
        value_err = Mock(side_effect=ValueError())
        with patch('stripe.Webhook.construct_event', value_err):
            resp = self.client.post(test_url, {'data':''},
                                    content_type='application/json',
                                    HTTP_STRIPE_SIGNATURE='SecretSignatureFromStripe')

        self.assertEqual(resp.status_code, 400)
        value_err.assert_called_once_with(bytes(json.dumps({'data': ''}), 'ascii'),
                                          'SecretSignatureFromStripe',
                                          settings.STRIPE_ENDPOINT_SECRET)
        self.user.refresh_from_db()
        self.assertEqual(self.user.subscription_expiration, expiration_base)

        stripe_err = Mock(side_effect=stripe.error.SignatureVerificationError('msg', 'header'))
        with patch('stripe.Webhook.construct_event', stripe_err):
            resp = self.client.post(test_url, {'data':''},
                                    content_type='application/json',
                                    HTTP_STRIPE_SIGNATURE='SecretSignatureFromStripe')

        self.assertEqual(resp.status_code, 400)
        stripe_err.assert_called_once_with(bytes(json.dumps({'data': ''}), 'ascii'),
                                          'SecretSignatureFromStripe',
                                          settings.STRIPE_ENDPOINT_SECRET)
        self.user.refresh_from_db()
        self.assertEqual(self.user.subscription_expiration, expiration_base)

        # make sure event type is checked
        def wrong_event(p, s, k):
            return {'type' : 'checkout.session.something',
                    'data': {'object': {'client_reference_id': checkout.pk}}}

        with patch('stripe.Webhook.construct_event', side_effect=wrong_event):
            resp = self.client.post(test_url, {'data':''},
                                    content_type='application/json',
                                    HTTP_STRIPE_SIGNATURE='SecretSignatureFromStripe')

        self.assertEqual(resp.status_code, 400)
        self.user.refresh_from_db()
        self.assertEqual(self.user.subscription_expiration, expiration_base)

        # make sure correct event works
        def correct_event(p, s, k):
            return {'type' : 'checkout.session.completed',
                    'data': {'object': {'client_reference_id': checkout.pk}}}

        with patch('stripe.Webhook.construct_event', side_effect=correct_event):
            resp = self.client.post(test_url, {'data':''},
                                    content_type='application/json',
                                    HTTP_STRIPE_SIGNATURE='SecretSignatureFromStripe')

        self.assertEqual(resp.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.subscription_expiration > expiration_base)
        checkout.refresh_from_db()
