import os
import environ
from pathlib import Path
from datetime import timedelta

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.1/howto/deployment/checklist/

env = environ.Env()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# environ.Env.read_env()
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env.str('SECRET_KEY')

# STRIPE : stripe keys
STRIPE_PUBLIC_KEY = env.str('STRIPE_PUBLIC_KEY')
STRIPE_SECRET_KEY = env.str('STRIPE_SECRET_KEY')
STRIPE_WEBHOOK_SECRET = env.str('STRIPE_WEBHOOK_SECRET')


STRIPE_SUCCESS_REDIRECT_URL = env.str('STRIPE_SUCCESS_REDIRECT_URL')
STRIPE_CANCEL_REDIRECT_URL = env.str('STRIPE_CANCEL_REDIRECT_URL')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env.bool('DEBUG', default=False)

# Allowed hosts
ALLOWED_HOSTS =  env.str('ALLOWED_HOSTS').split(" ")


# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_object_actions',
    'django_filters',
    'corsheaders',
    'djoser',
    'rest_framework',
    # 'debug_toolbar',
    'ckeditor',
    'ckeditor_uploader',
    'quizy',
    'startHere',
    'comments',
    'subscription',
    'core'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    # 'debug_toolbar.middleware.DebugToolbarMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


CORS_ALLOWED_ORIGINS = env.str('CORS_ALLOWED_ORIGINS').split(" ")

# CSRF_TRUSTED_ORIGINS = env.str('CSRF_TRUSTED_ORIGINS').split(" ")

# CORS_ORIGIN_ALLOW_ALL = True

ROOT_URLCONF = 'examination_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS':  [os.path.join(BASE_DIR, 'templates') ,os.path.join(BASE_DIR, 'core/dist')],
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

INTERNAL_IPS = [
    # ...
    "127.0.0.1",
    "192.168.1.102"
    # ...
]

WSGI_APPLICATION = 'examination_project.wsgi.application'

DATABASES = {'default': env.db('DATABASE_URL')}

# Password validation
# https://docs.djangoproject.com/en/4.1/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/4.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

USE_TZ = True

TIME_ZONE = 'UTC'

USE_I18N = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.1/howto/static-files/

MEDIA_URL = '/media/'
MEDIA_ROOT  = os.path.join(BASE_DIR, 'media')

STATIC_URL = '/static/'
# STATIC_ROOT = os.path.join(BASE_DIR, 'static')

if not DEBUG:
    # Tell Django to copy statics to the `staticfiles` directory
    # in your application directory on Render.
    STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

    # Turn on WhiteNoise storage backend that takes care of compressing static files
    # and creating unique names for each version so they can safely be cached forever.
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'


STATICFILES_DIRS = [
    os.path.join(BASE_DIR,'core/dist'),
]

# Default primary key field type
# https://docs.djangoproject.com/en/4.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


REST_FRAMEWORK = {
    'COERCE_DECIMAL_TO_STRING': False,
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
   'DEFAULT_PERMISSION_CLASSES' : [
      'rest_framework.permissions.IsAuthenticated'
    ]
}

SIMPLE_JWT = {
   'AUTH_HEADER_TYPES': ('JWT',),
   'ACCESS_TOKEN_LIFETIME': timedelta(days=90),
   'REFRESH_TOKEN_LIFETIME': timedelta(days=90),
}

AUTH_USER_MODEL = 'core.User'

DJOSER = {
       "PASSWORD_CHANGED_EMAIL_CONFIRMATION": True,
       "PASSWORD_RESET_CONFIRM_URL": "password/reset/confirm/{uid}/{token}",
       "LOGIN_FIELD": "email",
       'SERIALIZERS' : {
        'user_create': 'core.serializers.UserCreateSerializer',
        'user': 'core.serializers.UserSerializer',
        'current_user': 'core.serializers.UserSerializer',
    },
}


CKEDITOR_UPLOAD_PATH = 'uploads/'

CKEDITOR_CONFIGS = {
    'default': {
        'skin': 'moono',
        'toolbar' : 'all',
        'extraPlugins': ','.join([
            'widget',
            'dialog',
        ])
    }
}


EMAIL_BACKEND = env.str('EMAIL_BACKEND')
EMAIL_HOST = env.str('EMAIL_HOST')
EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS')
EMAIL_PORT = env.str('EMAIL_PORT')
EMAIL_HOST_USER = env.str('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = env.str('EMAIL_HOST_PASSWORD')
EMAIL_USE_SSL = env.bool('EMAIL_USE_SSL')