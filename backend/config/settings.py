import os
import sys
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from project root .env
load_dotenv(BASE_DIR.parent / '.env')

# Add parent directory to sys.path so we can import aviator_bot
sys.path.insert(0, str(BASE_DIR.parent))

# Allow background threads spawned by bot engines to perform sync database operations
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'django-insecure-aviator-bot-fallback-dev-key')
DEBUG = os.getenv('DJANGO_DEBUG', 'True').lower() in ('true', '1')

# Allowed Hosts (Permits localhost and local Wi-Fi LAN access)
raw_hosts = os.getenv('DJANGO_ALLOWED_HOSTS', '*')
ALLOWED_HOSTS = ['*'] if '*' in raw_hosts else [h.strip() for h in raw_hosts.split(',') if h.strip()]

INSTALLED_APPS = [
    'daphne',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'channels',
    'bot_engine',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

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
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'

# PostgreSQL Database Configuration from Environment (Supports DATABASE_URL for Appliku / Cloud)
database_url = os.getenv('DATABASE_URL', '')
if database_url:
    from urllib.parse import urlparse
    parsed_db = urlparse(database_url)
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': parsed_db.path[1:],
            'USER': parsed_db.username or '',
            'PASSWORD': parsed_db.password or '',
            'HOST': parsed_db.hostname or 'localhost',
            'PORT': str(parsed_db.port or 5432),
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.getenv('DB_NAME', 'aviator_db'),
            'USER': os.getenv('DB_USER', 'postgres'),
            'PASSWORD': os.getenv('DB_PASSWORD', ''),
            'HOST': os.getenv('DB_HOST', 'localhost'),
            'PORT': os.getenv('DB_PORT', '5432'),
        }
    }

# CSRF Trusted Origins for Cloud & Mobile Access
raw_csrf = os.getenv('CSRF_TRUSTED_ORIGINS', 'https://*.applikuapp.com,http://localhost:5173,http://localhost:8000,http://127.0.0.1:5173,http://127.0.0.1:8000')
CSRF_TRUSTED_ORIGINS = [o.strip() for o in raw_csrf.split(',') if o.strip()]

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# REST Framework Grade-A Security Configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'bot_engine.security.AdminApiKeyAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'bot_engine.security.IsAdminApiKey',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
        'rest_framework.throttling.ScopedRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '30/minute',
        'user': '120/minute',
        'bot_control': '15/minute',
        'ai_endpoints': '30/minute',
    },
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 50,
}

# CORS configuration (Allows local network and mobile devices)
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
    'x-api-key',
]

# Security Headers & Cookie Flags (Grade-A Defense)
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Lax'
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

# Channels in-memory channel layer for local WebSocket broadcasting
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer"
    }
}

# Grade-A Zero-Leak Logging Pipeline: scrubs all log messages across the entire Django process
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'security_scrubber': {
            '()': 'aviator_bot.security.log_filter.SecurityScrubberFilter',
        },

    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'filters': ['security_scrubber'],
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}

