import ast
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils import timezone
from datetime import timedelta


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
    email = models.EmailField('email address', unique=True)
    PLAN_CHOICES = [("basic", "Basic"), ("premium", "Premium")]
    plan = models.CharField(max_length=32, choices=PLAN_CHOICES, default="basic")
    last_active = models.DateTimeField(null=True )
    onboarding = models.BooleanField(default=True)
    _onboarding_sections = models.CharField(max_length=256,
                                            default="['dashboard', 'new_session', 'session_generate_1', 'session_validate', 'session_generate_2']")

    subscription_expiration = models.DateTimeField(null=False, default=timezone.now)

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

    def renew_subscription(self, mode: str = 'day', **kwargs):
        """
        Method for extending subscription period
        :param mode: Can be 'day', 'week', 'month', 'year'
        :param kwargs: 'datetime' to specify a time to which the subscription should be valid.
        :return:
        """
        if not 'datetime' in kwargs:
            now = timezone.now()
            if self.plan == 'basic':
                base = now
            else:
                base = self.subscription_expiration
            if mode == 'day':
                self.subscription_expiration = base + timedelta(days=1)
            elif mode == 'week':
                self.subscription_expiration = base + timedelta(days=7)
            elif mode == 'month':
                self.subscription_expiration = base + timedelta(days=31)
            elif mode == 'year':
                self.subscription_expiration = base + timedelta(days=365)
            else:
                raise ValueError('{} is an invalid mode. Valid modes are "day", "week", "month", "year"'.format(mode))
        else:
            self.subscription_expiration = kwargs['datetime']
        self.save()

    def expire(self):
        """
        Method for changing user plan from premium to basic
        :return:
        """
        self.plan = 'basic'
        self.save()
