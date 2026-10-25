import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Load KEY=VALUE pairs from the repo-root .env (git-ignored) without
# overriding variables already set in the environment.
_env_file = BASE_DIR.parent / '.env'
if _env_file.exists():
    for _line in _env_file.read_text().splitlines():
        _line = _line.strip()
        if _line and not _line.startswith('#') and '=' in _line:
            _key, _value = _line.split('=', 1)
            os.environ.setdefault(_key.strip(), _value.strip())

DEBUG = os.environ.get('DJANGO_DEBUG', '0') == '1'

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', '')
if not SECRET_KEY:
    if not DEBUG:
        raise RuntimeError('DJANGO_SECRET_KEY must be set when DJANGO_DEBUG is off.')
    SECRET_KEY = 'django-insecure-sandbox-dev-key-do-not-use-in-production'

ALLOWED_HOSTS = os.environ.get(
    'DJANGO_ALLOWED_HOSTS', 'blog-suite.lxcor.com,localhost,127.0.0.1'
).split(',')
CSRF_TRUSTED_ORIGINS = [f'https://{h}' for h in ALLOWED_HOSTS if h not in ('localhost', '127.0.0.1')]

if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_CONTENT_TYPE_NOSNIFF = True

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sitemaps',
    'postino',
    'dove',
    'core',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'postino.contextprocessors.postino',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'

# Defaults match the Sophia dev database; production overrides via .env
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DJANGO_DB_NAME', 'blogsuite'),
        'USER': os.environ.get('DJANGO_DB_USER', 'blogsuite'),
        'PASSWORD': os.environ.get('DJANGO_DB_PASSWORD', 'blogsuite'),
        'HOST': os.environ.get('DJANGO_DB_HOST', 'localhost'),
        'PORT': os.environ.get('DJANGO_DB_PORT', '5432'),
    }
}

LANGUAGE_CODE = 'en'
TIME_ZONE = 'America/Vancouver'
USE_I18N = True
USE_TZ = True

LANGUAGES = [
    ('en', 'English'),
    ('pt-br', 'Português (Brasil)'),
]

LOCALE_PATHS = [BASE_DIR / 'locale']

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Production mail goes through the box's local Postfix (SES relay)
EMAIL_BACKEND = os.environ.get(
    'DJANGO_EMAIL_BACKEND',
    'django.core.mail.backends.console.EmailBackend' if DEBUG
    else 'django.core.mail.backends.smtp.EmailBackend',
)
EMAIL_HOST = os.environ.get('DJANGO_EMAIL_HOST', 'localhost')
EMAIL_PORT = int(os.environ.get('DJANGO_EMAIL_PORT', '25'))
DEFAULT_FROM_EMAIL = os.environ.get('DJANGO_DEFAULT_FROM_EMAIL', 'Blog Suite <no-reply@lxcor.com>')
SERVER_EMAIL = DEFAULT_FROM_EMAIL

FIXTURE_DIRS = [BASE_DIR / 'fixtures']

# LLM settings for content gap → blog post pipeline
# Set POSTINO_LLM_PROVIDER to 'openai' or 'anthropic'
POSTINO_LLM_PROVIDER = os.environ.get('POSTINO_LLM_PROVIDER', 'openai')
POSTINO_LLM_MODEL = os.environ.get('POSTINO_LLM_MODEL', 'gpt-4o-mini')
POSTINO_LLM_API_KEY = os.environ.get('POSTINO_LLM_API_KEY', '')
# OpenAI reasoning models only (e.g. 'low' / 'medium'); replaces temperature when set
POSTINO_LLM_REASONING_EFFORT = os.environ.get('POSTINO_LLM_REASONING_EFFORT') or None

SESSION_COOKIE_NAME = 'sessionid_blog'

