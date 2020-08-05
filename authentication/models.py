import ast
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils import timezone
from datetime import timedelta, datetime
import pytz
from messaging import email
from .tokens import account_activation_token
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from payments.models import TaxationCountry, Subscription, RedeemedVoucher
from payments.countries import codes_iso3166
from django.conf import settings
from optimizer_api import api_client

from .choices import PLAN_CHOICES


class UserManager(BaseUserManager):
    """Define a model manager for User model with no username field."""

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """Create and save a User with the given email and password."""
        if not email:
            raise ValueError('The given email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular User with the given email and password."""
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        """Create and save a SuperUser with the given email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    """User model."""

    username = None
    email = models.EmailField('email address', unique=True,
                              error_messages={'unique': 'Email must be unique'})
    PLAN_CHOICES = [("basic", "Core"), ("premium", "Premium"), ("education", "Education"), ("permanent", "Permanent"), ("test", "Test"), ("limited", "Limited")]
    _plan = models.CharField(max_length=32, choices=PLAN_CHOICES, default="basic", db_column='plan')
    last_active = models.DateTimeField(null=True)
    onboarding = models.BooleanField(default=True)
    is_active = models.BooleanField(default=False)
    can_access_investor_dashboard = models.BooleanField(default=False)
    _onboarding_sections = models.CharField(max_length=256,
                                            default="['dashboard', 'new_session', 'session_generate_1', 'session_validate', 'session_generate_2']")

    subscription_expiration = models.DateTimeField(null=False, default=timezone.datetime(year=2020, day=10, month=4, tzinfo=pytz.utc))

    company_country = models.CharField(max_length=2, choices=codes_iso3166, blank=True)
    company_name = models.CharField(max_length=32, blank=True)
    company_legal_address = models.CharField(max_length=100, blank=True)
    company_registration_number = models.CharField(max_length=32, blank=True)
    company_vat_number = models.CharField(max_length=32, blank=True)

    manager_of_corporation = models.ForeignKey('payments.Corporation',
                                               null=True,
                                               blank=True,
                                               on_delete=models.SET_NULL,
                                               related_name='managers')
    member_of_corporation = models.ForeignKey('payments.Corporation',
                                              null=True,
                                              blank=True,
                                              on_delete=models.SET_NULL,
                                              related_name='team')

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    @property
    def available_tests(self):
        if self.plan == 'basic':
            return settings.FREE_TESTS
        else:
            return [test_number for test_number in api_client.get_routine()]

    @property
    def plan(self):
        if self.member_of_corporation is None:
            return self._plan

        return self.member_of_corporation.owner._plan

    @plan.setter
    def plan(self, val:str):
        if self.member_of_corporation is None or self.member_of_corporation.owner == self:
            self._plan = val


    @property
    def onboarding_sections(self):
        return ast.literal_eval(self._onboarding_sections)

    @onboarding_sections.setter
    def onboarding_sections(self, value: list):
        self._onboarding_sections = str(value)

    def onboarding_reset(self):
        self.onboarding = self._meta.get_field("onboarding").get_default()
        self._onboarding_sections = self._meta.get_field("_onboarding_sections").get_default()
        self.save()

    @property
    def plan_navbar_text(self):
        expiration_delta = self.subscription_expiration - timezone.now()
        if self.plan == 'basic':
            return "Upgrade to Full Access"
        elif self.plan == 'permanent':
            return "Permanent License"
        elif self.plan == "education":
            return "Student's License ({} Days)".format(expiration_delta.days + 1)
        elif self.plan == "premium":
            if len(Subscription.objects.filter(user=self, state__in=(Subscription.ACTIVE, Subscription.FAILURE_NOTIFIED))) == 0:
                return "Full Access ({} Days)".format(expiration_delta.days + 1)
            else:
                return "Full Access"
        elif self.plan == "test":
            return "Test Access ({} Days)".format(expiration_delta.days + 1)
        elif self.plan == "limited":
            return "Limited Access ({} Days)".format(expiration_delta.days + 1)

    def extend_subscription(self, delta: timedelta):
        """
        Method for extending subscription period
        :param delta: Time period that will be added to subscription
        :return:
        """
        base = max(self.subscription_expiration, timezone.now())
        new_date = base + delta
        if self.plan == 'limited':
            self.plan = 'premium'
        self.subscription_expiration = new_date.replace(hour=23, minute=59, second=59)
        self.save()

        try:
            redeemed = RedeemedVoucher.objects.get(user=self, visible_to_user=True)
        except RedeemedVoucher.DoesNotExist:
            return
        redeemed.visible_to_user = False
        redeemed.save()

    def subscribe_till(self, target_date:datetime):
        if self.plan == 'limited':
            self.plan = 'premium'
        self.subscription_expiration = target_date.replace(hour=23, minute=59, second=59)
        self.save()

        try:
            redeemed = RedeemedVoucher.objects.get(user=self, visible_to_user=True)
        except RedeemedVoucher.DoesNotExist:
            return
        redeemed.visible_to_user = False
        redeemed.save()

    def activate_account(self):
        self.is_active = True
        self.plan = 'limited'
        self.subscription_expiration = (timezone.now() + timedelta(days=7)).replace(hour=23, minute=59, second=59)
        self.save()


    def expire(self):
        """
        Method for changing user plan from premium to basic
        :return:
        """
        self.plan = 'basic'
        self.save()

    def send_account_activation(self, request):
        email.send_to_single(self.email, 'register_complete',
                             request,
                             receiving_user=' '.join((self.first_name,
                                                      self.last_name)),
                             uid=urlsafe_base64_encode(force_bytes(self.pk)),
                             token=account_activation_token.make_token(self)
                             )

    @property
    def is_company_account(self):
        if len(self.company_country) == 0:
            return False
        if len(self.company_name) == 0:
            return False
        if len(self.company_registration_number) == 0:
            return False
        return True

    @property
    def company_fields_accessible(self):
        return self.member_of_corporation is None or self.member_of_corporation.owner == self
    @property
    def can_collect_invoices(self):
        if not self.is_company_account:
            return False
        if len(TaxationCountry.objects.filter(pk=self.company_country)) == 0:
            return False
        return True

    @property
    def active_subscriptions(self):
        return self.subscription_set.filter(state__in=(Subscription.ACTIVE, Subscription.FAILURE_NOTIFIED))

    @property
    def client_of(self):
        try:
            redeemed = RedeemedVoucher.objects.get(user=self, visible_to_user=True)
        except RedeemedVoucher.DoesNotExist:
            return None
        if redeemed.voucher is None:
            redeemed.visible_to_user = False
            redeemed.save()
        return redeemed.voucher.partner

class Affiliate(models.Model):
    date_created = models.DateTimeField(auto_now_add=True, editable=False)
    date_registered = models.DateTimeField(editable=False, null=True)
    sender = models.ForeignKey('User', null=True, editable=False,
                                    on_delete=models.SET_NULL)
    corporation = models.ForeignKey('payments.Corporation', null=True,
                                    on_delete=models.SET_NULL)
    email = models.EmailField(null=False)
    name = models.CharField(max_length=30)
    message = models.TextField(default='', blank=True)
    receiver = models.ForeignKey('User', null=True, editable=False,
                                    on_delete=models.SET_NULL, default=None,
                                    related_name='invited_by')
    days_assigned = models.IntegerField(default=0)


    @property
    def is_confirmed(self):
        return self.days_assigned > 0

    def confirm(self, request):
        self.days_assigned = settings.AFFILIATE_BONUS_DAYS
        self.date_registered = timezone.now()
        self.save()

        if self.sender is None:
            return
        if self.corporation is not None:
            self.receiver.member_of_corporation = self.corporation
            self.receiver.save()
            self.corporation = None
            self.save()
            return

        self.sender.extend_subscription(timedelta(days=settings.AFFILIATE_BONUS_DAYS))

        email.send_to_single(self.sender.email, 'affiliate_confirmed', request,
                            affiliate=self)


        # notify requester about subscription extension


