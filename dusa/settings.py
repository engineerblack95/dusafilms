import os
from pathlib import Path
from dotenv import load_dotenv
import dj_database_url

# ==================================================
# BASE DIRECTORY
# ==================================================
BASE_DIR = Path(__file__).resolve().parent.parent

# ==================================================
# LOAD ENVIRONMENT VARIABLES
# ==================================================
load_dotenv(BASE_DIR / ".env")

# ==================================================
# SECURITY
# ==================================================
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "unsafe-dev-key")

DEBUG = os.getenv("DEBUG", "False") == "True"

# ==================================================
# HOST & PROXY (THIS FIXES 400 ERROR)
# ==================================================
ALLOWED_HOSTS = [
    "dusafilms.onrender.com",
    ".onrender.com",
    "localhost",
    "127.0.0.1",
]

USE_X_FORWARDED_HOST = True

CSRF_TRUSTED_ORIGINS = [
    "https://dusafilms.onrender.com",
]

# ==================================================
# APPLICATIONS
# ==================================================
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'django.contrib.postgres',

    'django_bootstrap5',
    'cloudinary',
    'cloudinary_storage',

    'anymail',
    'accounts',
    'movies',
    'contact',
    'announcements',
]

# ==================================================
# MIDDLEWARE
# ==================================================
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'dusa.urls'
WSGI_APPLICATION = 'dusa.wsgi.application'

# ==================================================
# TEMPLATES
# ==================================================
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / "templates"],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.template.context_processors.media',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'announcements.context_processors.unread_announcements',
            ],
        },
    },
]

# ===============================
# DATABASE CONFIG (LOCAL + RENDER)
# ===============================
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL and not DEBUG:
    # Production (Render)
    DATABASES = {
        "default": dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=600,
            ssl_require=True,
        )
    }
else:
    # Local development (PostgreSQL)
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.getenv('POSTGRES_DB', 'dusafilms'),
            'USER': os.getenv('POSTGRES_USER', 'Admin'),
            'PASSWORD': os.getenv('POSTGRES_PASSWORD', 'admin123'),
            'HOST': os.getenv('POSTGRES_HOST', 'localhost'),
            'PORT': os.getenv('POSTGRES_PORT', '5432'),
        }
    }

# ==================================================
# PASSWORD VALIDATION
# ==================================================
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ==================================================
# INTERNATIONALIZATION
# ==================================================
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Africa/Kigali'
USE_I18N = True
USE_TZ = True

# ==================================================
# STATIC FILES
# ==================================================
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# ==================================================
# CLOUDINARY (MEDIA STORAGE) — FIXED
# ==================================================
DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'

# ==================================================
# EMAIL (BREVO / SENDINBLUE)
# ==================================================
EMAIL_BACKEND = "anymail.backends.brevo.EmailBackend"

ANYMAIL = {
    "BREVO_API_KEY": os.getenv("BREVO_API_KEY"),
}

DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL")

# ==================================================
# PRODUCTION SECURITY
# ==================================================
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

# ==================================================
# DEFAULT AUTO FIELD
# ==================================================
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ==================================================
# LOGGING (Render logs)
# ==================================================
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'ERROR',
    },
}
