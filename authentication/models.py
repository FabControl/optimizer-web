import ast
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils import timezone
from datetime import timedelta
import pytz
from messaging import email
from .tokens import account_activation_token
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes


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
    PLAN_CHOICES = [("basic", "Core"), ("premium", "Premium"), ("education", "Education"), ("permanent", "Permanent"), ("test", "Test")]
    plan = models.CharField(max_length=32, choices=PLAN_CHOICES, default="basic")
    # Time limited subscription types:
    time_limited_plans = ['premium', 'education', 'test']
    last_active = models.DateTimeField(null=True)
    onboarding = models.BooleanField(default=True)
    is_active = models.BooleanField(default=False)
    can_access_investor_dashboard = models.BooleanField(default=False)
    _onboarding_sections = models.CharField(max_length=256,
                                            default="['dashboard', 'new_session', 'session_generate_1', 'session_validate', 'session_generate_2']")

    subscription_expiration = models.DateTimeField(null=False, default=timezone.datetime(year=2020, day=30, month=4, tzinfo=pytz.utc))

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

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
            return "Permanent license"
        elif self.plan == "education":
            return "Student's license ({} days)".format(expiration_delta.days + 1)
        elif self.plan == "premium":
            return "Full access ({} days)".format(expiration_delta.days + 1)
        elif self.plan == "test":
            return "Test access ({} days)".format(expiration_delta.days + 1)

    def extend_subscription(self, delta: timedelta):
        """
        Method for extending subscription period
        :param delta: Time period that will be added to subscription
        :return:
        """
        base = max(self.subscription_expiration, timezone.now())
        new_date = base + delta
        self.subscription_expiration = new_date.replace(hour=23, minute=59, second=59)
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
