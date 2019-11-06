from django.db import models
from datetime import timedelta
from authentication.models import User


class Plan(models.Model):
    name = models.CharField(max_length=32, default="Untitled Plan")
    price = models.DecimalField(default=None, null=True, decimal_places=2, max_digits=6)
    subscription_period = models.DurationField(default=timedelta(days=31))
    type = models.CharField(max_length=32, choices=(('premium', 'Premium'), ('basic', 'Basic')), default='basic')

    def __str__(self):
        return "{} ({})".format(self.name, '{} Eur'.format(self.price) if self.price != 0 else "Free")
