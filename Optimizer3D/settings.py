"""
Django settings for Optimizer3D project.

Generated by 'django-admin startproject' using Django 2.2.2.

For more information on this file, see
https://docs.djangoproject.com/en/2.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.2/ref/settings/
"""

import os
from os import environ
from django.utils.translation import gettext_lazy as _

_selected_settings = environ.get('SELECTED_SETTINGS', 'PRODUCTION')
if _selected_settings == 'PRODUCTION':
    from .configuration_settings.settings_production import *
elif _selected_settings == 'TESTING':
    from .configuration_settings.settings_test import *


# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'session.apps.SessionConfig',
    'payments.apps.PaymentsConfig',
    'django_simple_cookie_consent.apps.DjangoSimpleCookieConsentConfig',
    'authentication.apps.AuthenticationConfig',
    'crispy_forms',
    'rosetta'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'authentication.middleware.translation.SiteLocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'Optimizer3D.middleware.GeoRestrictAccessMiddleware.GeoRestrictAccessMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'Optimizer3D.middleware.EnforceSubscriptionMiddleware.enforce_subscription_middleware',
    'payments.middleware.NotifySubscriptionChargeFailuresMiddleware.notify_failures_middleware'
]

ROOT_URLCONF = 'Optimizer3D.urls'

LOGIN_URL = "/login/"

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            'templates/'
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'Optimizer3D.context_processors.ga_tracking_id',
            ],
        },
    },
]

CRISPY_TEMPLATE_PACK = 'bootstrap4'

WSGI_APPLICATION = 'Optimizer3D.wsgi.application'

# Password validation
# https://docs.djangoproject.com/en/2.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

AUTH_USER_MODEL = 'authentication.User'

# Internationalization
# https://docs.djangoproject.com/en/2.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Europe/Riga'

DATETIME_FORMAT = 'N j Y H:i'

USE_I18N = True

LANGUAGES = (
        ('en', _('English')),
        ('lv', _('Latvian')),
        )
LOCALE_PATHS = [
        os.path.join(BASE_DIR, 'locale')
        ]

# USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.2/howto/static-files/

STATIC_URL = '/static/'

STATIC_ROOT = os.path.join(BASE_DIR, 'static')

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'views': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
        },
        'django': {
              'handlers': ['console'],
              'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
          },
    },
}

PASSWORD_RESET_TIMEOUT_DAYS = 1

SAMPLE_SESSIONS_OWNER = 'sample_settings_user@fabcontrol.com'

DEVELOPERS = [
        'aivars@fabcontrol.com',
        'egils@fabcontrol.com',
        ]

TIME_LIMITED_PLANS = ['education', 'premium', 'test', 'limited']

PAYMENTS_COMPANY_NAME = 'SIA "FabControl"'
PAYMENTS_COMPANY_REG_NUMBER = '40203151106'
PAYMENTS_COMPANY_VAT_NUMBER = 'LV40203151106'
# No more than two lines
PAYMENTS_COMPANY_ADDRESS = ['Pulka iela 3, Rīga, LV-1007',
        'Latvia']
PAYMENTS_COMPANY_BANK = 'Luminor Bank AS Latvian branch'
PAYMENTS_COMPANY_SWIFT = 'NDEALV2X'
PAYMENTS_COMPANY_ACCOUNT = 'LV59NDEA0000085924321'

AFFILIATE_BONUS_DAYS = 7
SUBSCRIPTION_EXTRA_DAYS = 5

FREE_TESTS = ['01', '03', '10']

MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'

