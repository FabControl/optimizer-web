from django.db import models
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
import uuid
from django.contrib.auth import get_user_model
from .countries import codes_iso3166


class Plan(models.Model):
    name = models.CharField(max_length=32, default="Untitled Plan")
    price = models.DecimalField(default=None, null=True, decimal_places=2, max_digits=6)
    subscription_period = models.DurationField(default=timedelta(days=31))
    type = models.CharField(max_length=32, choices=(('corporate', 'Corporate'), ('premium', 'Premium'), ('basic', 'Basic'), ('deleted', 'Deleted')), default='basic')

    @property
    def pretty_price(self):
        return str(self.price).replace('.00', ',-')

    def __str__(self):
        return "{} ({})".format(self.name, '{} Eur'.format(self.price) if self.price != 0 else "Free")


def get_sentinel_plan():
    return Plan.objects.filter(type='deleted')[0]


def get_sentinel_user():
        return get_user_model().objects.get(email='deleted@user.com')


class Checkout(models.Model):
    checkout_id = models.CharField(max_length=40,
                                   primary_key=True,
                                   unique=True,
                                   default=uuid.uuid4,
                                   editable=False)
    stripe_id = models.CharField(max_length=100,
                                 blank=True,
                                 unique=True,
                                 editable=False)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    is_paid = models.BooleanField(blank=True, default=False, editable=False)
    is_cancelled = models.BooleanField(blank=True, default=False, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                            on_delete=models.SET(get_sentinel_user),
                            editable=False)
    payment_plan = models.ForeignKey('Plan',
                            on_delete=models.SET(get_sentinel_plan),
                            editable=False)
    invoice = models.ForeignKey('Invoice', on_delete=models.SET_NULL, null=True)

    @property
    def is_expired(self):
        if self.is_paid or self.is_cancelled:
            return False
        return timezone.now() > self.created + timedelta(days=1)

    def confirm_payment(self):
        self.user.extend_subscription(self.payment_plan.subscription_period)
        self.is_paid = True
        self.invoice = Invoice.objects.create()
        self.save()

    def cancel(self):
        if not (self.is_paid or self.is_expired):
            self.is_cancelled = True
            self.save()

    @property
    def invoice_number(self):
        if self.invoice is None:
            return ''
        return 'INV_{0}_{1:03}'.format(self.created.strftime('%Y-%m'),
                                       self.invoice.pk)


class Invoice(models.Model):
    pass

class TaxationCountry(models.Model):
    name = models.CharField(max_length=2, choices=codes_iso3166, primary_key=True)
    vat_charge = models.DecimalField(decimal_places=0, max_digits=2, default=21,
                                            help_text='In percents from full price')
    exclude_vat = models.BooleanField(default=False,
                                      help_text='Check this, if companies with VAT number should have 0% VAT charge (EU only)')
    @property
    def long_name(self):
        for x in codes_iso3166: 
            if x[0] == self.name:
                return x[1]

    def __str__(self):
        return f'{self.long_name} (VAT={self.vat_charge}%)'
