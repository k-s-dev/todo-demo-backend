"""
Django settings for dj_conf project.

Generated by 'django-admin startproject' using Django 5.1.3.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.1/ref/settings/
"""

import os
import environ

from .base import *

# create and read environs env
env = environ.Env()
env.read_env(os.path.join(BASE_DIR, '.env.prod'))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env("DEBUG", cast=bool, default=False)
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", [])

CSRF_COOKIE_SECURE = env("CSRF_COOKIE_SECURE", cast=bool, default=True)
SESSION_COOKIE_SECURE = env("SESSION_COOKIE_SECURE", cast=bool, default=True)
SECURE_SSL_REDIRECT = env("SECURE_SSL_REDIRECT", cast=bool, default=True)
# https://docs.djangoproject.com/en/5.0/ref/settings/#secure-ssl-redirect
# change below if needed, read above section in docs
# SECURE_PROXY_SSL_HEADER = None

