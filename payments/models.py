from django.db import models
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
import pytz
import uuid
from django.contrib.auth import get_user_model
from .countries import codes_iso3166
import zlib
from base64 import b64encode, b64decode
from django.forms.models import model_to_dict


class ModelDiffMixin(object):
    """
    A model mixin that tracks model fields' values and provide some useful api
    to know what fields have been changed.
    """

    def __init__(self, *args, **kwargs):
        super(ModelDiffMixin, self).__init__(*args, **kwargs)
        self.__initial = self._dict

    @property
    def diff(self):
        d1 = self.__initial
        d2 = self._dict
        diffs = [(k, (v, d2[k])) for k, v in d1.items() if v != d2[k]]
        return dict(diffs)

    @property
    def has_changed(self):
        return bool(self.diff)

    @property
    def changed_fields(self):
        return self.diff.keys()

    def get_field_diff(self, field_name):
        """
        Returns a diff for field if it's changed and None otherwise.
        """
        return self.diff.get(field_name, None)

    def save(self, *args, **kwargs):
        """
        Saves model and set initial state.
        """
        super(ModelDiffMixin, self).save(*args, **kwargs)
        self.__initial = self._dict

    @property
    def _dict(self):
        return model_to_dict(self, fields=[field.name for field in self._meta.fields])


class Plan(ModelDiffMixin, models.Model):
    name = models.CharField(max_length=32, default="Untitled Plan")
    price = models.DecimalField(default=None, null=True, decimal_places=2, max_digits=6)
    subscription_period = models.DurationField(default=timedelta(days=31))
    type = models.CharField(max_length=32, choices=(('corporate', 'Corporate'), ('premium', 'Premium'), ('basic', 'Basic'), ('deleted', 'Deleted')), default='basic')
    stripe_plan_id = models.CharField(max_length=32, default="", editable=False)

    @property
    def is_one_time(self):
        return self.stripe_plan_id == ''

    @property
    def pretty_price(self):
        return str(self.price).replace('.00', ',-')

    def __str__(self):
        return "{} ({})".format(self.name, ('{} Eur '.format(self.price) + ("One-Time" if self.is_one_time else "Subscription")) if self.price != 0 else "Free")

    @classmethod
    def from_stripe(cls, stripe_plan:dict):
        try:
            plan = cls.objects.get(stripe_plan_id=stripe_plan['id'])
        except cls.DoesNotExist:
            plan = cls(type='premium', stripe_plan_id=stripe_plan['id'])

        plan.name = stripe_plan['nickname']
        plan.price = stripe_plan['amount'] / 100.0
        # subscriptin_period does not matter, since stripe is handling subscription extension
        return plan



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


class Invoice(models.Model):
    _backups = models.TextField(null=False, default='')
    _one_time_payment = models.ForeignKey('Checkout',
                                            on_delete=models.SET_NULL,
                                            null=True,
                                            related_name='paid_invoice',
                                            editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                            on_delete=models.SET(get_sentinel_user),
                            editable=False,
                            null=True)
    date_paid = models.DateTimeField(auto_now_add=True, editable=False)

    @property
    def invoice_number(self):
        return 'INV_{0}_{1:03}'.format(self.date_paid.astimezone(pytz.utc).strftime('%Y-%m'),
                                       self.pk)

    @property
    def payment_plan(self):
        if self._one_time_payment is not None:
            return self._one_time_payment.payment_plan
        return None

    @property
    def backup_count(self):
        return self._backups.count('\n')

    def get_backup(self, index):
        data = zlib.decompress(b64decode(self._backups.split('\n')[index].encode()))
        return data.decode()

    def store_backup(self, html_invoice):
        data = b64encode(zlib.compress(html_invoice.encode())).decode()
        for l in self._backups.split('\n'):
            if l == data:
                return
        self._backups += data + '\n'
        self.save()


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
