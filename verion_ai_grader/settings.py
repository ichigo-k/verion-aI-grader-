"""
Django settings for verion_ai_grader project.
"""

import json
import os
from pathlib import Path

import dj_database_url
from django.core.exceptions import ImproperlyConfigured

# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _require_env(name: str) -> str:
    """Return the value of a required environment variable or raise."""
    value = os.environ.get(name)
    if not value:
        raise ImproperlyConfigured(
            f"Required environment variable '{name}' is not set."
        )
    return value


# ---------------------------------------------------------------------------
# Build paths
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# Required environment variables
# ---------------------------------------------------------------------------

DATABASE_URL = _require_env('DATABASE_URL')
AWS_ACCESS_KEY_ID = _require_env('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = _require_env('AWS_SECRET_ACCESS_KEY')
AWS_REGION = _require_env('AWS_REGION')
BEDROCK_MODEL_ID = _require_env('BEDROCK_MODEL_ID')

# ---------------------------------------------------------------------------
# Security
# ---------------------------------------------------------------------------

SECRET_KEY = _require_env('DJANGO_SECRET_KEY')

DEBUG = os.environ.get('DEBUG', 'False') == 'True'

_allowed_hosts_env = os.environ.get('ALLOWED_HOSTS', '')
if _allowed_hosts_env:
    ALLOWED_HOSTS = [h.strip() for h in _allowed_hosts_env.split(',') if h.strip()]
elif DEBUG:
    ALLOWED_HOSTS = ['*']
else:
    ALLOWED_HOSTS = []

# ---------------------------------------------------------------------------
# Application definition
# ---------------------------------------------------------------------------

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'rest_framework',
    'grader',
    'auth_keys',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'verion_ai_grader.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
            ],
        },
    },
]

WSGI_APPLICATION = 'verion_ai_grader.wsgi.application'

# ---------------------------------------------------------------------------
# Database (task 1.5)
# ---------------------------------------------------------------------------

DATABASES = {
    'default': dj_database_url.config(default=DATABASE_URL, conn_max_age=600)
}

# ---------------------------------------------------------------------------
# Django REST Framework (task 1.6)
# ---------------------------------------------------------------------------

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'auth_keys.authentication.ApiKeyAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}

# ---------------------------------------------------------------------------
# Internationalisation
# ---------------------------------------------------------------------------

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ---------------------------------------------------------------------------
# Optional environment variables with validation
# ---------------------------------------------------------------------------

# GRADING_SCALE — JSON string, e.g. '{"A": 70, "B": 60, "C": 50, "D": 40}'
_grading_scale_raw = os.environ.get('GRADING_SCALE', '{"A": 70, "B": 60, "C": 50, "D": 40}')
try:
    GRADING_SCALE: dict = json.loads(_grading_scale_raw)
except json.JSONDecodeError as exc:
    raise ImproperlyConfigured(
        f"Environment variable 'GRADING_SCALE' is not valid JSON: {exc}"
    ) from exc

# BEDROCK_MAX_TOKENS — integer, default 2048
_bedrock_max_tokens_raw = os.environ.get('BEDROCK_MAX_TOKENS', '2048')
try:
    BEDROCK_MAX_TOKENS: int = int(_bedrock_max_tokens_raw)
except ValueError as exc:
    raise ImproperlyConfigured(
        f"Environment variable 'BEDROCK_MAX_TOKENS' must be a valid integer, "
        f"got: '{_bedrock_max_tokens_raw}'"
    ) from exc

# GRADING_CONCURRENCY — integer, default 10
_grading_concurrency_raw = os.environ.get('GRADING_CONCURRENCY', '10')
try:
    GRADING_CONCURRENCY: int = int(_grading_concurrency_raw)
except ValueError as exc:
    raise ImproperlyConfigured(
        f"Environment variable 'GRADING_CONCURRENCY' must be a valid integer, "
        f"got: '{_grading_concurrency_raw}'"
    ) from exc
