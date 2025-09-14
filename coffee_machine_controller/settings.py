import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'your-secret-key-here')
DEBUG = os.getenv('DJANGO_DEBUG', 'False').lower() == 'true'
ALLOWED_HOSTS = ['*']  # Allow all hosts for Home Assistant Add-on

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'channels',
    'machine',
    'api',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'machine.middleware.DisableCSRFForAPI',  # Add before CsrfViewMiddleware
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'coffee_machine_controller.urls'

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

WSGI_APPLICATION = 'coffee_machine_controller.wsgi.application'
ASGI_APPLICATION = 'coffee_machine_controller.asgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': '/data/db.sqlite3' if os.path.exists('/data') else BASE_DIR / 'db.sqlite3',
    }
}

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser',
    ],
}

# CORS settings - Allow Home Assistant and local access
CORS_ALLOWED_ORIGINS = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://homeassistant.local:8123",
    "http://supervisor",
]
# Allow all origins for Home Assistant Add-on environment
CORS_ALLOW_ALL_ORIGINS = True

# CSRF settings for Home Assistant proxy/ingress
CSRF_TRUSTED_ORIGINS = [
    'http://homeassistant.local:8123',
    'http://supervisor',
    'http://localhost:8000',
    'http://127.0.0.1:8000',
    'https://*.ui.nabu.casa',
    'https://xrqlxhrnom02wtf3cfz3odga9u80vpyc.ui.nabu.casa',
]

# Additional proxy settings for ingress
USE_X_FORWARDED_HOST = os.getenv('USE_X_FORWARDED_HOST', 'True').lower() == 'true'
USE_X_FORWARDED_PORT = os.getenv('USE_X_FORWARDED_PORT', 'True').lower() == 'true'
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Force script name for ingress paths
FORCE_SCRIPT_NAME = os.getenv('FORCE_SCRIPT_NAME', None)

# Static files with ingress support
STATIC_URL = os.getenv('FORCE_SCRIPT_NAME', '') + '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Coffee Machine Settings
COFFEE_MACHINE_PORT = os.getenv('COFFEE_MACHINE_PORT', '/dev/serial/by-id/usb-FTDI_FT232R_USB_UART_BG01CG7P-if00-port0')  # Your coffee machine port on Raspberry Pi
COFFEE_MACHINE_BAUDRATE = int(os.getenv('COFFEE_MACHINE_BAUDRATE', '9600'))

# Celery Configuration
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'

# Channels Configuration
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [('127.0.0.1', 6379)],
        },
    },
}

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
            'class': 'logging.FileHandler',
            'filename': '/data/coffee_machine.log' if os.path.exists('/data') else 'coffee_machine.log',
        },
        'console': {
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'machine': {
            'handlers': ['file', 'console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
            'propagate': True,
        },
        'django': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
            'propagate': True,
        },
    },
}