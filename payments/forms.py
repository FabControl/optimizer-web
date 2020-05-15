from django import forms
from .models import Checkout, Plan, Currency
import stripe
from django.http.request import HttpRequest
from django.urls import reverse
from .countries import codes_iso3166


class PaymentPlanForm(forms.Form):
    plan_id = forms.IntegerField()

    class Meta:
        fields = ['plan_id']

    def create_invoice(self, user, request:HttpRequest):
        base_url = 'https://' + request.META['HTTP_HOST']
        plan = Plan.objects.get(pk=self.cleaned_data.get('plan_id'))
        checkout = Checkout(user=user, payment_plan=plan)

        if plan.is_one_time:
            items={'line_items': [{ 'name': '3DOptimizer full access {0.name}'.format(plan),
                                    'description': 'Full access to all 3DOptimizer features',
                                    'amount': int(plan.price * 100), # price in cents
                                    'currency': 'eur',
                                    'quantity': 1}]}
        else:
            items={'subscription_data':{ 'items': [{'plan': plan.stripe_plan_id}],
                                        'metadata': {'internal_reference': checkout.pk}}}

        bill = stripe.checkout.Session.create(
                payment_method_types=['card'],
                customer_email=user.email,
                client_reference_id=checkout.checkout_id,
                success_url=base_url + reverse('checkout_completed', args=[checkout.checkout_id]),
                cancel_url=base_url + reverse('checkout_cancelled', args=[checkout.checkout_id]),
                **items)

        if plan.is_one_time:
            checkout.stripe_id = bill['payment_intent']
        else:
            checkout.stripe_id = bill['id']
        checkout.save()

        return bill['id']

class CurrencyAdminForm(forms.ModelForm):
    countries = forms.MultipleChoiceField(choices=codes_iso3166, widget=forms.widgets.CheckboxSelectMultiple)
    class Meta:
        model = Currency
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        if 'instance' in kwargs:
            if 'initial' not in kwargs or kwargs['initial'] is None:
                kwargs['initial'] = {}

            kwargs['initial']['countries'] = kwargs['instance'].countries

        return super().__init__(*args, **kwargs)

    def save(self, commit=True):
        result = super().save(commit=False)
        result.countries = self.cleaned_data['countries']
        if commit:
            result.save()
        return result
