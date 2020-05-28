from django.db import models
from django.utils import timezone
from datetime import timedelta, datetime
from django.conf import settings
import pytz
import uuid
from django.contrib.auth import get_user_model
from .countries import codes_iso3166, codes_iso4217
import zlib
from base64 import b64encode, b64decode
from django.forms.models import model_to_dict
import stripe


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
    currency = models.ForeignKey('Currency', on_delete=models.CASCADE, default='EUR')
    max_users_allowed = models.PositiveIntegerField(default=0)
    extra_info_text = models.TextField(default='', blank=True)

    @property
    def extra_info_text_lines(self):
        if self.extra_info_text == '':
            return []
        return self.extra_info_text.split('\n')
    @property
    def is_one_time(self):
        return self.stripe_plan_id == ''

    @property
    def payment_frequency_string(self):
        if self.is_one_time:
            return 'One-time payment'
        if self.name in ('Month', 'Year'):
            return f'Recurring {self.name}ly payment'
        return 'Recurring payment'


    @property
    def pretty_price(self):
        return str(self.price).replace('.00', ',-')

    def __str__(self):
        if self.price == 0:
            return "{} (Free)".format(self.name)

        info = 'One-Time' if self.is_one_time else 'Subscription'
        info += f' {self.price} {self.currency.name}'
        return "{} ({})".format(self.name, info)


    @classmethod
    def from_stripe(cls, stripe_plan:dict):
        try:
            plan = cls.objects.get(stripe_plan_id=stripe_plan['id'])
        except cls.DoesNotExist:
            plan = cls(stripe_plan_id=stripe_plan['id'])
            if stripe_plan['product'] == settings.STRIPE_BUSINESS_PRODUCT_ID:
                plan.max_users_allowed = 5


        try:
            currency = Currency.objects.get(name=stripe_plan['currency'].upper())
        except Currency.DoesNotExist:
            currency = Currency.objects.create(name=stripe_plan['currency'].upper())

        plan.name = stripe_plan['nickname']
        plan.price = stripe_plan['amount'] / 100.0
        if stripe_plan['active']:
            plan.type = 'corporate' if stripe_plan['product'] == settings.STRIPE_BUSINESS_PRODUCT_ID else 'premium'
        else:
            plan.type = 'deleted'
        plan.currency = currency
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
        if self.is_paid:
            return

        self.user.extend_subscription(self.payment_plan.subscription_period)
        self.is_paid = True
        Invoice.objects.create(_one_time_payment=self, user=self.user)
        self.save()

    def cancel(self):
        if not (self.is_paid or self.is_expired):
            self.is_cancelled = True
            self.save()

class Subscription(models.Model):
    PENDING = 'incomplete'
    ACTIVE = 'active'
    CHARGE_FAILED = 'past_due'
    FAILURE_NOTIFIED = 'failure_notified'
    CANCELLED = 'canceled'
    EXPIRED = 'incomplete_expired'

    created = models.DateTimeField(auto_now_add=True, editable=False)
    paid_till = models.DateTimeField(auto_now_add=True, editable=False)
    stripe_id = models.CharField(max_length=32, editable=False)
    state = models.CharField(max_length=32, default=PENDING, editable=False,
                            choices=[(ACTIVE, 'Active'),
                                     (PENDING, 'First payment pending'),
                                     (EXPIRED, 'First payment expired'),
                                     (CHARGE_FAILED, 'Charge failed'),
                                     (FAILURE_NOTIFIED, 'Failure notified'),
                                     (CANCELLED, 'Cancelled')])

    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                            on_delete=models.SET(get_sentinel_user),
                            editable=False)
    payment_plan = models.ForeignKey('Plan',
                            on_delete=models.SET(get_sentinel_plan),
                            editable=False)

    @classmethod
    def update_from_stripe(cls, stripe_data:dict):
        subscription = cls.objects.get(stripe_id=stripe_data['id'])
        if stripe_data['status'] != cls.PENDING:
            subscription.state = stripe_data['status']

        if subscription.state == cls.ACTIVE:
            paid = datetime.fromtimestamp(stripe_data['current_period_end'], timezone.utc)
            if subscription.paid_till < paid:
                subscription.user.subscribe_till(paid + timedelta(days=settings.SUBSCRIPTION_EXTRA_DAYS))
                subscription.paid_till = paid
                Invoice.objects.create(_subscription=subscription, user=subscription.user)

        subscription.save()

    @property
    def card_info(self):
        subscription = stripe.Subscription.retrieve(self.stripe_id)
        payment_method_id = subscription['default_payment_method']
        if payment_method_id is None:
            payment_method_id = stripe.Customer.retrieve(subscription['customer'])['invoice_settings']['default_payment_method']

        card = stripe.PaymentMethod.retrieve(payment_method_id)['card']
        return card['brand'] + ' ****' + card['last4']

class Currency(models.Model):
    name = models.CharField(max_length=3,
                            editable=True,
                            choices=codes_iso4217, 
                            primary_key=True)
    _countries = models.CharField(max_length=600, editable=False, default='')

    @property
    def countries(self):
        return self._countries.split(' ')

    @countries.setter
    def countries(self, country_list:list):
        self._countries = ' '.join(country_list)

    def __str__(self):
        return f'{self.name} in {len(self.countries)} countries'


class Invoice(models.Model):
    _backups = models.TextField(null=False, default='')
    _subscription = models.ForeignKey('Subscription',
                                            on_delete=models.SET_NULL,
                                            null=True,
                                            related_name='paid_invoice',
                                            editable=False)

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
        if self._subscription is not None:
            return self._subscription.payment_plan
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

class Corporation(models.Model):
    name = models.CharField(max_length=32)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    _invited_users = models.CharField(max_length=500, default='', blank=True)

    @property
    def invited_users(self):
        return get_user_model().objects.filter(email__in=self._invited_users.split(' '))

    def invite_user(self, user):
        if ' ' + user.email + ' ' not in self._invited_users:
            if len(self._invited_users) < 1:
                self._invited_users = ' '
            self._invited_users += user.email + ' '
            self.save()


    def remove_invitation(self, user):
        self._invited_users = self._invited_users.replace(user.email + ' ', '')
        self.save()

    @property
    def allow_invites(self):
        return self.max_allowed > self.user_count

    @property
    def team_sorted(self):
        return self.team.all().order_by(models.F('corporation').desc(nulls_first=False))

    @property
    def user_count(self):
        return len(self.team.all()) + len(self.invited_users) + len(self.affiliate_set.all())
    @property
    def max_allowed(self):
        if self.owner.plan != 'premium':
            return self.user_count
        try:
            plan = self.owner.subscription_set.get(state__in=(Subscription.ACTIVE, Subscription.FAILURE_NOTIFIED)).payment_plan
        except Subscription.DoesNotExist:
            return self.user_count

        if plan.type != 'corporate':
            return self.user_count

        return plan.max_users_allowed
