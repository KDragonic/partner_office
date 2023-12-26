import os
from pathlib import Path
import django
from django.utils.encoding import smart_str
django.utils.encoding.smart_text = smart_str

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# BASE_DIR = "/"


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "###"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ADMINS = [('DEV', 'denkoropov@gmail.com')]

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'formatters': {
        'django.server': {
            '()': 'django.utils.log.ServerFormatter',
            'format': '[{server_time}] {message}',
            'style': '{',
        }
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'filters': ['require_debug_true'],
            'class': 'logging.StreamHandler',
        },
        'django.server': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'django.server',
        },
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler',
            'include_html': True
        }
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'mail_admins'],
            'level': 'INFO',
        },
        'django.server': {
            'handlers': ['django.server'],
            'level': 'INFO',
            'propagate': False,
        },
    }
}

ALLOWED_HOSTS = [
    "turgorodok.ru",
    "188.93.211.116",
    "127.0.0.1",
]

TELEGRAMBOT_TOKEN = "5774730521:AAE7ZJ-Pn__fFBvCCCaIdGFjZvHNVYUy2qA"

ADMIN_URL = "django_admin/"
DATA_UPLOAD_MAX_NUMBER_FIELDS = 10240 # higher than the count of fields

SITE_ID = 1

#Почта
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_SSL = True
EMAIL_USE_TLS = False
EMAIL_HOST_USER = 'turgorodok@gmail.com'
EMAIL_HOST_PASSWORD = 'turgorodok500#'

SERVER_EMAIL = EMAIL_HOST_USER
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER


#Вк
VK_APP_ID = 51619666
VK_SECURE_KEY = "f1p2nkIIqkohKk7ldnvY"

#Google
# ID проэкта turgorodok-384418
CLIENT_SECRET_FILE = "client_secret.json"


#QR
QR_CERT_PATH = "client_cert.crt"
QR_CERT_PASSWORD = "4srYdebg4z"


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.sitemaps',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'debug_toolbar',
    'django_json_widget',
    'main',
    'hotel',
    'chat',
    'technical_support',
    'utils',
    'bot',
    'partner',
    'user',
    'crispy_forms',
    'django.contrib.humanize',
    'django_extensions',
    'sass_processor',
    'mptt',
    'tinymce',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'utils.middleware.AdminLogMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
]

def show_toolbar(request):
    return False
    # if not request.user.is_authenticated:
    #     return False

    # return request.user.id == 1

DEBUG_TOOLBAR_CONFIG = {
    'SHOW_TOOLBAR_CALLBACK': show_toolbar,
}

GRAPH_MODELS = {
  'all_applications': True,
  'group_models': True,
}

GRAPH_MODELS = {
  'app_labels': ["hotel", "chat", "technical_support", "utils", "user"],
}

ROOT_URLCONF = 'brontur.urls'

AUTH_USER_MODEL = "user.User"

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / "templates",
        ],
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

WSGI_APPLICATION = 'brontur.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.db.DatabaseCache",
        "LOCATION": "cache_table",
    }
}


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

TELEGRAM_BOT_API_KEY="5774730521:AAE7ZJ-Pn__fFBvCCCaIdGFjZvHNVYUy2qA"

# Internationalization
# https://docs.djangoproject.com/en/4.1/topics/i18n/

LOGIN_URL = "/login/"

LANGUAGE_CODE = 'ru-RU'
USE_I18N = True

TIME_ZONE = 'Europe/Moscow'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.1/howto/static-files/


STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'static'

# STATICFILES_DIRS = [
#     os.path.join(BASE_DIR, 'staticfiles'),
#     os.path.join(BASE_DIR, 'staticfiles/scss/'),
# ]


MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# DATA_UPLOAD_MAX_NUMBER_FIELDS = 100000

STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'sass_processor.finders.CssFinder',
]

# MEDIA_URL = '/media/'
# MEDIA_ROOT = 'media/'

LOGIN_REDIRECT_URL = '/page_back_url_login_page/'

# Default primary key field type
# https://docs.djangoproject.com/en/4.1/ref/settings/#default-auto-field