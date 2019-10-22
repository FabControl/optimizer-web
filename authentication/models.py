import ast
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
# Create your models here.


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
    onboarding = models.BooleanField(default=True)
    _onboarding_sections = models.CharField(max_length=256,
                                            default="['dashboard', 'new_session', 'session_generate_1', 'session_validate', 'session_generate_2']")

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    @property
    def onboarding_sections(self):
        return ast.literal_eval(self._onboarding_sections)

    @onboarding_sections.setter
    def onboarding_sections(self, value: list):
        self._onboarding_sections = str(value)
