from decouple import config
import os
from pathlib import Path
import logging

try:
    import dj_database_url
except ImportError:
    dj_database_url = None

try:
    from google.oauth2 import service_account
except ImportError:
    service_account = None

BASE_DIR = Path(__file__).resolve().parent.parent

# Environment detection
IS_RENDER = config('RENDER', default=False, cast=bool)

# GCS Configuration (only for non-Render environments)
if not IS_RENDER and service_account:
    try:
        GCS_BUCKET_NAME = config('GCS_BUCKET_NAME')
        SERVICE_ACCOUNT_FILE = os.path.join(BASE_DIR, config('GCS_SERVICE_ACCOUNT_KEY'))
        GCP_PROJECT_ID = config('GCP_PROJECT_ID')
        
        if os.path.exists(SERVICE_ACCOUNT_FILE):
            GS_CREDENTIALS = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE)
    except Exception as e:
        print(f"GCS configuration error: {e}")
        GCS_BUCKET_NAME = None
        SERVICE_ACCOUNT_FILE = None
        GCP_PROJECT_ID = None

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY', default='django-insecure-default-key-change-in-production')
DEBUG = config('DEBUG', default=False, cast=bool)

# Host configuration
ALLOWED_HOSTS = ['*']  # Allow all hosts for simplicity in Render

# HTTPS settings (only for non-Render environments)
if not IS_RENDER:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = False  # Redirect all HTTP requests to HTTPS
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

# Application definition
INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'corsheaders',
    'rest_framework',
    'currency',
    'gold',
    'predicts',
    'finnomenaGold',
    'data',
    'logging_app',
    'django_extensions',
    'Utility',
]

# Redis configuration for different environments
if IS_RENDER:
    # Use external Redis service (Upstash) for Render
    REDIS_URL = config('REDIS_URL', default=None)
    if REDIS_URL:
        CACHES = {
            "default": {
                "BACKEND": "django_redis.cache.RedisCache",
                "LOCATION": REDIS_URL,
                "OPTIONS": {
                    "CLIENT_CLASS": "django_redis.client.DefaultClient",
                    "CONNECTION_POOL_KWARGS": {
                        "ssl_cert_reqs": None,
                        "ssl_check_hostname": False,
                    }
                }
            }
        }
    else:
        # Fallback to locmem cache (faster than database cache)
        CACHES = {
            "default": {
                "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
                "LOCATION": "unique-snowflake",
                "OPTIONS": {
                    "MAX_ENTRIES": 1000,
                    "CULL_FREQUENCY": 3,
                }
            }
        }
elif os.environ.get('IS_DOCKER_ENV') == 'true':
    REDIS_HOST = os.environ.get('REDIS_HOST', 'redis')
    REDIS_PORT = os.environ.get('REDIS_PORT', '6379')
    REDIS_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}"
    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": f"{REDIS_URL}/1",
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
            }
        }
    }
else:
    REDIS_HOST = 'redis://127.0.0.1:6379'
    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": f"{REDIS_HOST}/1",
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
            }
        }
    }

# Logging Configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'debug.log'),
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'currency': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# ตั้งค่า CORS ให้ทุกเครื่องสามารถเรียกใช้ API ได้
CORS_ALLOW_ALL_ORIGINS = True  # อนุญาตการเข้าถึงจากทุกที่

# อนุญาตทุก method
CORS_ALLOW_METHODS = [
    "GET",
    "POST",
    "PUT",
    "PATCH",
    "DELETE",
    "OPTIONS",
]

# อนุญาต header ที่จำเป็น
CORS_ALLOW_HEADERS = [
    "accept",
    "accept-encoding",
    "authorization",
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
]

# Explicitly allow credentials (cookies, authorization headers, etc)
CORS_ALLOW_CREDENTIALS = True

# เปลี่ยนลำดับ middleware ให้ corsheaders อยู่ด้านบน
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',  # ต้องอยู่ตำแหน่งแรก
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # สำหรับ static files บน Render
    # 'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    # 'django.middleware.csrf.CsrfViewMiddleware',
    # 'django.contrib.auth.middleware.AuthenticationMiddleware',
    # 'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'Backend.urls'

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

WSGI_APPLICATION = 'Backend.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

if IS_RENDER and dj_database_url:
    # Use PostgreSQL from Render with environment variable
    DATABASES = {
        'default': dj_database_url.parse(config('DATABASE_URL'))
    }
else:
    # Use custom PostgreSQL configuration
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': config('DB_NAME'),
            'USER': config('DB_USER'),
            'PASSWORD': config('DB_PASSWORD'),
            'HOST': config('DB_HOST'),
            'PORT': config('DB_PORT', cast=int),
        }
    }

# GCS Configuration (only for non-Render environments)
if not IS_RENDER and service_account and 'GCS_BUCKET_NAME' in locals():
    try:
        # Load credentials if file exists
        if SERVICE_ACCOUNT_FILE and os.path.exists(SERVICE_ACCOUNT_FILE):
            credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE)
    except Exception as e:
        print(f"GCS credentials loading error: {e}")

# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Bangkok'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Additional static files directories
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
] if os.path.exists(os.path.join(BASE_DIR, 'static')) else []

# WhiteNoise configuration for static files
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'