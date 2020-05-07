"""
###################################################
THIS FILE CONTAINS TESTING SPECIFIC SETTINGS
###################################################

Django settings for Optimizer3D project.

Generated by 'django-admin startproject' using Django 2.2.2.

For more information on this file, see
https://docs.djangoproject.com/en/2.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.2/ref/settings/
"""
import os


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "This should be hidden, but it isn't"

ALLOWED_HOSTS = ['local.test.domain']
# Database
# https://docs.djangoproject.com/en/2.2/ref/settings/#databases

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

EMAIL_SENDER_ADDRESS = 'noreply@some.test.domain'

STRIPE_API_KEY = 'Some very secret key'
STRIPE_PUBLIC_KEY = 'Some not so secret key'
STRIPE_ENDPOINT_SECRET = 'Another secret key'
STRIPE_SUBSCRIPTION_PRODUCT_ID = 'Product id here'

GA_TRACKING_ID = 'UA_STEAL_ALL_YOR_DATA'
