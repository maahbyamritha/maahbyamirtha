"""Production settings. Secrets and hostnames are supplied by the host."""
import os
from django.core.exceptions import ImproperlyConfigured
import dj_database_url
from .settings import *  # noqa: F403

DEBUG = False
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', '')
if len(SECRET_KEY) < 50 or SECRET_KEY.startswith('django-insecure-'):
    raise ImproperlyConfigured('Set a strong DJANGO_SECRET_KEY for production.')

ALLOWED_HOSTS = [host.strip() for host in os.environ.get('DJANGO_ALLOWED_HOSTS', '').split(',') if host.strip()]
if os.environ.get('RENDER_EXTERNAL_HOSTNAME'):
    ALLOWED_HOSTS.append(os.environ['RENDER_EXTERNAL_HOSTNAME'])
if not ALLOWED_HOSTS or '*' in ALLOWED_HOSTS:
    raise ImproperlyConfigured('Set explicit production hostnames.')
CSRF_TRUSTED_ORIGINS = ['https://' + host for host in ALLOWED_HOSTS]

if not os.environ.get('DATABASE_URL'):
    raise ImproperlyConfigured('Set DATABASE_URL to a persistent PostgreSQL database.')
DATABASES = {'default': dj_database_url.parse(os.environ['DATABASE_URL'], conn_max_age=60)}
MIDDLEWARE = list(MIDDLEWARE)  # noqa: F405
MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')
STATIC_ROOT = BASE_DIR / 'staticfiles'  # noqa: F405
STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage'},
}
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 3600
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True

if not SHOPIFY_STORE_DOMAIN or not SHOPIFY_STOREFRONT_PRIVATE_TOKEN:  # noqa: F405
    raise ImproperlyConfigured('Set Shopify storefront credentials on the hosting service.')

# The storefront currently sends no email. Configure SMTP before enabling
# password resets or other email-based features.
MAILERS = {'default': {
    'BACKEND': 'django.core.mail.backends.smtp.EmailBackend',
    'OPTIONS': {
        'host': os.environ.get('SMTP_HOST', 'localhost'),
        'port': int(os.environ.get('SMTP_PORT', '587')),
        'username': os.environ.get('SMTP_USERNAME', ''),
        'password': os.environ.get('SMTP_PASSWORD', ''),
        'use_tls': True,
        'timeout': 10,
    },
}}
