from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.conf import settings
from django.utils import timezone, html
from uuid import uuid4
import json
import stripe
from unittest.mock import Mock, patch
from payments.models import Plan, Checkout
from datetime import timedelta
from copy import deepcopy


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
        result_timestamp_min = (max(current_expiration, timezone.now()) + plan.subscription_period).replace(hour=23, minute=59, second=59)

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
            resp = c.post(reverse('handle_stripe_event'), {'data': ''})
        self.assertEqual(resp.status_code, 200)

        # check subscription expiration time
        self.user.refresh_from_db()
        result_timestamp_max = (max(current_expiration, timezone.now()) + plan.subscription_period).replace(hour=23, minute=59, second=59)

        self.assertTrue(self.user.subscription_expiration >= result_timestamp_min)
        self.assertTrue(self.user.subscription_expiration <= result_timestamp_max)

    def test_webhook_validation(self):
        test_url = reverse('handle_stripe_event')
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

    def test_checkout_cancellation(self):
        self.user.refresh_from_db()
        expiration_base = self.user.subscription_expiration
        # create test checkout
        checkout = Checkout(user=self.user,
                            stripe_id=uuid4(),
                            payment_plan=self.plans[2])

        checkout.save()
        test_url = reverse('checkout_cancelled', args=[checkout.checkout_id])

        # check if only logged in users can cancel their checkouts
        resp = self.client.get(test_url, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.redirect_chain[-1][0],
                         '?next='.join((reverse('login'), test_url)))

        # check if you can't cancel other user's checkout
        usr = get_user_model().objects.create_user(email='other_user@somewhere.com',
                                is_active=True,
                                password='OtherSecretPassword')
        self.assertTrue(self.client.login(email='other_user@somewhere.com',
                                password='OtherSecretPassword'))
        resp = self.client.get(test_url)

        self.assertEqual(resp.status_code, 404)
        checkout.refresh_from_db()
        self.user.refresh_from_db()
        self.assertFalse(checkout.is_cancelled)
        self.assertEqual(self.user.subscription_expiration, expiration_base)

        usr.delete()

        # check if expired checkout can't be cancelled
        self.assertTrue(self.client.login(email='known_user@somewhere.com',
                                            password='SomeSecretPassword'))

        def two_days_later(): return checkout.created + timedelta(days=2)

        with patch('django.utils.timezone.now', side_effect=two_days_later):
            resp = self.client.get(test_url, follow=True)

        self.assertEqual(resp.status_code, 200)
        checkout.refresh_from_db()
        self.user.refresh_from_db()
        self.assertFalse(checkout.is_cancelled)
        self.assertEqual(self.user.subscription_expiration, expiration_base)
        self.assertTrue(b'Your checkout session has expired' in resp.content)

        # check if checkout can be cancelled
        resp = self.client.get(test_url, follow=True)

        self.assertEqual(resp.status_code, 200)
        checkout.refresh_from_db()
        self.user.refresh_from_db()
        self.assertTrue(checkout.is_cancelled)
        self.assertEqual(self.user.subscription_expiration, expiration_base)

    def test_completed_message(self):
        self.user.refresh_from_db()
        expiration_base = self.user.subscription_expiration
        # create test checkout
        checkout = Checkout(user=self.user,
                            stripe_id=uuid4(),
                            payment_plan=self.plans[2])

        checkout.save()
        test_url = reverse('checkout_completed', args=[checkout.checkout_id])

        # check if only logged in users can access their checkouts
        resp = self.client.get(test_url, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.redirect_chain[-1][0],
                         '?next='.join((reverse('login'), test_url)))

        checkout.refresh_from_db()
        self.user.refresh_from_db()
        self.assertFalse(checkout.is_paid)
        self.assertEqual(self.user.subscription_expiration, expiration_base)

        # check if you can't see messages from other checkouts
        usr = get_user_model().objects.create_user(email='other_user@somewhere.com',
                                is_active=True,
                                password='OtherSecretPassword')
        self.assertTrue(self.client.login(email='other_user@somewhere.com',
                                password='OtherSecretPassword'))
        resp = self.client.get(test_url)

        self.assertEqual(resp.status_code, 404)
        checkout.refresh_from_db()
        self.user.refresh_from_db()
        self.assertFalse(checkout.is_paid)
        self.assertEqual(self.user.subscription_expiration, expiration_base)

        usr.delete()

        # check if checkout links expire
        self.assertTrue(self.client.login(email='known_user@somewhere.com',
                                            password='SomeSecretPassword'))

        def two_days_later(): return checkout.created + timedelta(days=2)

        with patch('django.utils.timezone.now', side_effect=two_days_later):
            resp = self.client.get(test_url, follow=True)

        self.assertEqual(resp.status_code, 200)
        checkout.refresh_from_db()
        self.user.refresh_from_db()
        self.assertFalse(checkout.is_paid)
        self.assertEqual(self.user.subscription_expiration, expiration_base)
        self.assertTrue(b'Your checkout session has expired' in resp.content)

        # check warning message, if not confirmed
        resp = self.client.get(test_url, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.redirect_chain[-1][0], reverse('plans'))
        checkout.refresh_from_db()
        self.user.refresh_from_db()
        self.assertFalse(checkout.is_paid)
        self.assertEqual(self.user.subscription_expiration, expiration_base)
        msg = html.escape('We haven\'t received your payment yet. Please check after few minutes')
        self.assertTrue(bytes(msg, 'ascii') in resp.content)

        # notify about checkout completion
        def correct_event(p, s, k):
            return {'type' : 'checkout.session.completed',
                    'data': {'object': {'client_reference_id': checkout.pk}}}

        with patch('stripe.Webhook.construct_event', side_effect=correct_event):
            resp = self.client.post(reverse('handle_stripe_event'), {'data':''},
                                    content_type='application/json',
                                    HTTP_STRIPE_SIGNATURE='SecretSignatureFromStripe')

        self.assertEqual(resp.status_code, 200)

        # check success message on confirmed payment
        resp = self.client.get(test_url, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.redirect_chain[-1][0], reverse('plans'))

        msg = html.escape('Your full access was extended for {0.days} days'.format(checkout.payment_plan.subscription_period))
        self.assertTrue(bytes(msg, 'ascii') in resp.content)

        checkout.refresh_from_db()
        self.user.refresh_from_db()
        self.assertTrue(checkout.is_paid)
        self.assertTrue(self.user.subscription_expiration > expiration_base)

class StripeHookHandlerTest(TestCase):
    @classmethod
    def setUpClass(self):
        self.url = reverse('handle_stripe_event')

    @classmethod
    def tearDownClass(self):
        pass

    def test_payment_plan_updates(self):
        event = {
            "id": "evt_1Gg8DAIyp4fvmVpEmtwbfBF8",
            "object": "event",
            "api_version": "2019-11-05",
            "created": 1588852100,
            "data": {
                "object": {
                    "id": "plan_HEbQWLvbXgOTM3",
                    "object": "plan",
                    "active": True,
                    "aggregate_usage": None,
                    "amount": 200,
                    "amount_decimal": "200",
                    "billing_scheme": "per_unit",
                    "created": 1588852100,
                    "currency": "eur",
                    "interval": "month",
                    "interval_count": 1,
                    "livemode": False,
                    "metadata": {
                        },
                    "nickname": "Some plan",
                    "product": "prod_HDoK9LmTymCvzj",
                    "tiers": None,
                    "tiers_mode": None,
                    "transform_usage": None,
                    "trial_period_days": None,
                    "usage_type": "licensed"
                    }
                },
            "livemode": False,
            "pending_webhooks": 2,
            "request": {
                "id": "req_KssFb78f4XSgBx",
                "idempotency_key": None
                },
            "type": "plan.created"
            }

        stripe_plan = event['data']['object']
        # create arbitrary plan
        Plan.objects.create()
        plan_count = len(Plan.objects.all())
        # create new plan from stripe with different product id
        with patch('stripe.Webhook.construct_event', return_value=deepcopy(event)):
            resp = self.client.post(self.url, {'data':''},
                                    content_type='application/json',
                                    HTTP_STRIPE_SIGNATURE='SecretSignatureFromStripe')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(plan_count, len(Plan.objects.all()))

        # create plan with correct product id
        stripe_plan['product'] = settings.STRIPE_SUBSCRIPTION_PRODUCT_ID
        with patch('stripe.Webhook.construct_event', return_value=deepcopy(event)):
            resp = self.client.post(self.url, {'data':''},
                                    content_type='application/json',
                                    HTTP_STRIPE_SIGNATURE='SecretSignatureFromStripe')
        self.assertEqual(resp.status_code, 200)
        plan_count += 1
        self.assertEqual(plan_count, len(Plan.objects.all()))
        # if plan creaeted correctly, this should not fail
        Plan.objects.get(name=stripe_plan['nickname'],
                        price=stripe_plan['amount'] / 100.0,
                        type='premium',
                        stripe_plan_id=stripe_plan['id'])

        # post same event, to check new plan creation
        with patch('stripe.Webhook.construct_event', return_value=deepcopy(event)):
            resp = self.client.post(self.url, {'data':''},
                                    content_type='application/json',
                                    HTTP_STRIPE_SIGNATURE='SecretSignatureFromStripe')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(plan_count, len(Plan.objects.all()))
        # if plan was not created again, this should not fail
        Plan.objects.get(name=stripe_plan['nickname'],
                        price=stripe_plan['amount'] / 100.0,
                        type='premium',
                        stripe_plan_id=stripe_plan['id'])

        # update plan
        stripe_plan['nickname'] = 'Updated stripe plan'
        event['type'] = 'plan.updated'
        with patch('stripe.Webhook.construct_event', return_value=deepcopy(event)):
            resp = self.client.post(self.url, {'data':''},
                                    content_type='application/json',
                                    HTTP_STRIPE_SIGNATURE='SecretSignatureFromStripe')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(plan_count, len(Plan.objects.all()))
        # if plan updated correctly, this should not fail
        Plan.objects.get(name=stripe_plan['nickname'],
                        price=stripe_plan['amount'] / 100.0,
                        type='premium',
                        stripe_plan_id=stripe_plan['id'])

        # make plan inactive
        stripe_plan['active'] = False
        with patch('stripe.Webhook.construct_event', return_value=deepcopy(event)):
            resp = self.client.post(self.url, {'data':''},
                                    content_type='application/json',
                                    HTTP_STRIPE_SIGNATURE='SecretSignatureFromStripe')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(plan_count, len(Plan.objects.all()))
        # if plan disabled correctly, this should not fail
        Plan.objects.get(name=stripe_plan['nickname'],
                        price=stripe_plan['amount'] / 100.0,
                        type='deleted',
                        stripe_plan_id=stripe_plan['id'])
        # delete plan
        event['type'] = 'plan.deleted'
        with patch('stripe.Webhook.construct_event', return_value=deepcopy(event)):
            resp = self.client.post(self.url, {'data':''},
                                    content_type='application/json',
                                    HTTP_STRIPE_SIGNATURE='SecretSignatureFromStripe')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(plan_count, len(Plan.objects.all()))
        # plan should not actually be deleted
        Plan.objects.get(name=stripe_plan['nickname'],
                        price=stripe_plan['amount'] / 100.0,
                        type='deleted',
                        stripe_plan_id=stripe_plan['id'])


