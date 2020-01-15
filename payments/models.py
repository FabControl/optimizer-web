from django.db import models
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
import uuid


class Plan(models.Model):
    name = models.CharField(max_length=32, default="Untitled Plan")
    price = models.DecimalField(default=None, null=True, decimal_places=2, max_digits=6)
    subscription_period = models.DurationField(default=timedelta(days=31))
    type = models.CharField(max_length=32, choices=(('corporate', 'Corporate'), ('premium', 'Premium'), ('basic', 'Basic')), default='basic')

    @property
    def pretty_price(self):
        return str(self.price).replace('.00', ',-')

    def __str__(self):
        return "{} ({})".format(self.name, '{} Eur'.format(self.price) if self.price != 0 else "Free")



def get_sentinel_plan():
        return Plan.get_or_create(name='deleted')[0]

def get_sentinel_user():
        return settings.AUTH_USER_MODEL.get_or_create(email='deleted@user.com')[0]


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
        self.save()

    def cancel(self):
        if not (self.is_paid or self.is_expired):
            self.is_cancelled = True
            self.save()
