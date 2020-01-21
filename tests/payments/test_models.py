from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.conf import settings
from payments.models import Plan, Checkout


class PaymentCheckoutTest(TestCase):
    def test_linked_data_deletion(self):
        plan = Plan.objects.create(type='premium')
        user = get_user_model().objects.create(email='some@user.com')
        checkout = Checkout.objects.create(user=user, payment_plan=plan)

        plan.delete()
        checkout.refresh_from_db()
        self.assertTrue(checkout.payment_plan != plan)

        user.delete()
        checkout.refresh_from_db()
        self.assertTrue(checkout.user != user)
