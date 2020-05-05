from django import forms
from .models import Checkout, Plan
import stripe
from django.http.request import HttpRequest
from django.urls import reverse


class PaymentPlanForm(forms.Form):
    plan_id = forms.IntegerField()

    class Meta:
        fields = ['plan_id']

    def create_invoice(self, user, request:HttpRequest):
        base_url = 'https://' + request.META['HTTP_HOST']
        plan = Plan.objects.get(pk=self.cleaned_data.get('plan_id'))
        checkout = Checkout(user=user, payment_plan=plan)

        bill = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'name': '3DOptimizer full access {0.name}'.format(plan),
                    'description': 'Full access to all 3DOptimizer features',
                    'amount': int(plan.price * 100), # price in cents
                    'currency': 'eur',
                    'quantity': 1,
                    }],
                customer_email=user.email,
                client_reference_id=checkout.checkout_id,
                success_url=base_url + reverse('checkout_completed', args=[checkout.checkout_id]),
                cancel_url=base_url + reverse('checkout_cancelled', args=[checkout.checkout_id]))

        checkout.stripe_id = bill['payment_intent']
        checkout.save()

        return bill['id']
