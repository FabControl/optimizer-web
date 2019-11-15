"""
###################################################
THIS FILE CONTAINS PRODUCTION SPECIFIC SETTINGS
###################################################

Django settings for Optimizer3D project.

Generated by 'django-admin startproject' using Django 2.2.2.

For more information on this file, see
https://docs.djangoproject.com/en/2.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.2/ref/settings/
"""

import os
from config import config

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config["SECRET_KEY"]


ALLOWED_HOSTS = [config['APP_HOST']]
if 'DB_HOST' in config:
    ALLOWED_HOSTS.append(config['DB_HOST'])

# Database
# https://docs.djangoproject.com/en/2.2/ref/settings/#databases

if 'DB_HOST' in config:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.' + config['DB_ENGINE'],
            'HOST': config['DB_HOST'],
            'PORT': config['DB_PORT'],
            'USER': config['DB_USERNAME'],
            'PASSWORD': config['DB_PASSWORD'],
            'NAME': config['DB_NAME']
        }
    }
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
        }
    }

EMAIL_HOST_PASSWORD = config['EMAIL_HOST_PASSWORD']
EMAIL_HOST_USER = config['EMAIL_HOST_USER']
EMAIL_HOST = config['EMAIL_HOST']
EMAIL_SENDER_ADDRESS = 'noreply@' + config['APP_HOST']

STRIPE_API_KEY = config['STRIPE_API_PRIVATE_KEY']
STRIPE_PUBLIC_KEY = config['STRIPE_API_PUBLIC_KEY']
STRIPE_ENDPOINT_SECRET = config['STRIPE_ENDPOINT_SECRET']
