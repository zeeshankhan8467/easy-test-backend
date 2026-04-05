"""
Django settings for easytest project.
"""

from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-change-this-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1,127.0.0.1:5174').split(',')

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'api',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

CORS_ALLOW_ALL_ORIGINS = True

ROOT_URLCONF = 'easytest.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'easytest.wsgi.application'

# Database - use SQLite when DB_ENGINE=sqlite (e.g. when MySQL is not running)
if os.getenv('DB_ENGINE', '').lower() == 'sqlite':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': os.getenv('DB_NAME', 'easytest'),
            'USER': os.getenv('DB_USER', 'root'),
            'PASSWORD': os.getenv('DB_PASSWORD', ''),
            'HOST': os.getenv('DB_HOST', '127.0.0.1'),
            'PORT': os.getenv('DB_PORT', '3306'),
            'OPTIONS': {
                'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
                'charset': 'utf8mb4',
            },
        }
    }

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
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

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Django REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 100,
}

# JWT Settings
from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# CORS Settings - allow frontend dev servers (localhost and 127.0.0.1)
_default_origins = [
    'http://localhost:5173',
    'http://localhost:3000',
    'http://127.0.0.1:5173',
    'http://127.0.0.1:3000',
]
CORS_ALLOWED_ORIGINS = [
    o.strip() for o in os.getenv(
        'CORS_ALLOWED_ORIGINS',
        ','.join(_default_origins)
    ).split(',') if o.strip()
] or _default_origins

CORS_ALLOW_CREDENTIALS = True

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Email (SMTP)
# If EMAIL_HOST is configured, we use SMTP even when DEBUG=True.
_email_host_default = 'smtp.gmail.com'
_email_port_default = '587'
_email_use_tls_default = 'True'
_email_host_user_default = 'easytest1988@gmail.com'
# Gmail app passwords are sometimes pasted/shown as groups with spaces.
# Store the default without whitespace, and also strip whitespace if loaded from env.
_email_host_password_default = 'rxrdoenzbflnsnrb'
_default_from_email_default = 'yourgmail@gmail.com'

_email_host = (os.getenv('EMAIL_HOST', _email_host_default) or '').strip()
_email_port = (os.getenv('EMAIL_PORT', _email_port_default) or '').strip()
_email_host_user = (os.getenv('EMAIL_HOST_USER', _email_host_user_default) or '').strip()
_email_host_password = (os.getenv('EMAIL_HOST_PASSWORD', _email_host_password_default) or '').strip()

# Remove all whitespace so SMTP receives the correct raw password.
_email_host_password = ''.join(_email_host_password.split())

EMAIL_HOST = _email_host
EMAIL_PORT = int(_email_port) if _email_port.isdigit() else 587
EMAIL_HOST_USER = _email_host_user
EMAIL_HOST_PASSWORD = _email_host_password
EMAIL_USE_TLS = (os.getenv('EMAIL_USE_TLS', _email_use_tls_default) or '').strip().lower() in ('1', 'true', 'yes', 'on')
DEFAULT_FROM_EMAIL = (os.getenv('DEFAULT_FROM_EMAIL', _default_from_email_default) or '').strip()

# SMTP connect timeout (seconds). Keeps gunicorn workers from hanging on network blocks.
EMAIL_TIMEOUT = int((os.getenv('EMAIL_TIMEOUT', '10') or '').strip() or '10')

# Always use SMTP so the "send email to parent" feature works in dev.
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

# Logging: ensure our time-tracking debug logs from `api.views` are visible in dev.
# Without this, Django's default logging often suppresses `logger.info(...)` output.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {
            'format': '[{levelname}] {name}: {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'api.views': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
