from .base import *

DEBUG = True

ALLOWED_HOSTS = ["localhost", "127.0.0.1"]
SITE_URL = "http://localhost:8000"

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

CSRF_TRUSTED_ORIGINS = ["http://localhost", "http://127.0.0.1"]
