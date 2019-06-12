"""
Django settings for the Resolwe server.

"""
import os
import re
import sys
from distutils.util import strtobool


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'set-this-in-production'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework.authtoken',
    'rest_framework_reactive',
    'rest_auth',
    'guardian',
    'versionfield',
    'corsheaders',
    'channels',
    'django_filters',
    'resolwe',
    'resolwe.permissions',
    'resolwe.flow',
    'resolwe.elastic',
    'resolwe.toolkit',
    'resolwe_server.base',
    'resolwe_server.uploader',
]

MIDDLEWARE = [
    'django.contrib.sessions.middleware.SessionMiddleware',
    # 'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
]

ROOT_URLCONF = 'resolwe_server.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.template.context_processors.static',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ]
        },
    }
]

WSGI_APPLICATION = 'resolwe_server.wsgi.application'

# Password validation

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'
    },
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)

STATIC_URL = '/static/'

# CORS

CORS_ORIGIN_REGEX_WHITELIST = (
    r'^(https?:\/\/)?(\w+\.)?(localhost|127.0.0.1)(:\d+)$',)

CORS_ALLOW_CREDENTIALS = True

CORS_ALLOW_HEADERS = (
    'x-requested-with',
    'content-type',
    'accept',
    'origin',
    'authorization',
    'x-csrftoken',
    'session-id',
    'x-file-uid',
)

# Database

DATABASES = {
    'default': {
        'ENGINE': 'django_db_geventpool.backends.postgresql_psycopg2',
        'NAME': 'resolwe-server',
        'USER': 'resolwe-server',
        'HOST': 'localhost',
        'PORT': 55432,
        'CONN_MAX_AGE': 0,
        'OPTIONS': {'MAX_CONNS': 20},
    }
}

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'guardian.backends.ObjectPermissionBackend',
)

ANONYMOUS_USER_NAME = 'AnonymousUser'

# Redis

REDIS_CONNECTION = {
    'host': 'localhost',
    'port': int(os.environ.get('RESOLWE_REDIS_PORT', 56379)),
    'db': int(os.environ.get('RESOLWE_REDIS_DATABASE', 1)),
}

# Resolwe

FLOW_EXECUTOR = {
    'NAME': 'resolwe.flow.executors.docker',
    'DATA_DIR': os.path.join(PROJECT_ROOT, 'data', 'data'),
    'UPLOAD_DIR': os.path.join(PROJECT_ROOT, 'data', 'upload'),
    'RUNTIME_DIR': os.path.join(PROJECT_ROOT, 'data', 'runtime'),
    'CONTAINER_IMAGE': 'resolwe/base:ubuntu-18.04',
    'REDIS_CONNECTION': REDIS_CONNECTION,
}

manager_prefix = 'resolwe-server.manager'

FLOW_MANAGER = {
    'REDIS_PREFIX': manager_prefix,
    'REDIS_CONNECTION': REDIS_CONNECTION,
    'TEST': {'REDIS_PREFIX': manager_prefix + '-test'},
    'DISPATCHER_MAPPING': {
        'Interactive': 'resolwe.flow.managers.workload_connectors.celery',
        'Batch': 'resolwe.flow.managers.workload_connectors.celery',
    },
}

# Don't pull Docker images up front
FLOW_DOCKER_DONT_PULL = True

FLOW_API = {'PERMISSIONS': 'resolwe.permissions.permissions'}
FLOW_EXPRESSION_ENGINES = [
    {'ENGINE': 'resolwe.flow.expression_engines.jinja', 'CUSTOM_FILTERS': []}
]
FLOW_EXECUTION_ENGINES = [
    'resolwe.flow.execution_engines.bash',
    'resolwe.flow.execution_engines.workflow',
    'resolwe.flow.execution_engines.python',
]


FLOW_PROCESSES_FINDERS = (
    'resolwe.flow.finders.FileSystemProcessesFinder',
    'resolwe.flow.finders.AppDirectoriesFinder',
)

FLOW_PROCESSES_DIRS = (os.path.join(
    PROJECT_ROOT, 'resolwe_server', 'processes'),)

FLOW_DESCRIPTORS_DIRS = (os.path.join(
    PROJECT_ROOT, 'resolwe_server', 'descriptors'),)

RESOLWE_CUSTOM_TOOLS_PATHS = [os.path.join(
    PROJECT_ROOT, 'resolwe_server', 'tools')]

FLOW_DOCKER_VOLUME_EXTRA_OPTIONS = {
    'data': 'Z',
    'data_all': 'z',
    'upload': 'z',
    'secrets': 'Z',
    'users': 'Z',
    'tools': 'z',
}

FLOW_DOCKER_EXTRA_VOLUMES = []

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_FILTER_BACKENDS': (
        'rest_framework_filters.backends.DjangoFilterBackend',
        'resolwe_server.base.filters.JsonOrderingFilter',
        'resolwe.permissions.filters.ResolwePermissionsFilter',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
    'EXCEPTION_HANDLER': 'resolwe.flow.utils.exceptions.resolwe_exception_handler',
    'TEST_REQUEST_DEFAULT_FORMAT': 'json',
}

BROKER_URL = 'redis://{host}:{port}/{db}'.format(**REDIS_CONNECTION)

WS4REDIS_CONNECTION = REDIS_CONNECTION

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://{host}:{port}/{db}'.format(**REDIS_CONNECTION),
        'OPTIONS': {'CLIENT_CLASS': 'django_redis.client.DefaultClient'},
    }
}

ELASTICSEARCH_HOST = os.environ.get('RESOLWE_ES_HOST', 'localhost')
ELASTICSEARCH_PORT = int(os.environ.get('RESOLWE_ES_PORT', '59200'))

# Channels

manager_channels_re = re.compile(r'^{}.*'.format(FLOW_MANAGER['REDIS_PREFIX']))

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [(REDIS_CONNECTION['host'], REDIS_CONNECTION['port'])],
            'expiry': 3600,
            'channel_capacity': {
                # Make sure no 'communicate' call is dropped.
                manager_channels_re: 10000
            },
        },
    }
}

ASGI_APPLICATION = 'resolwe_server.routing.application'

# channels_config = CHANNEL_LAYERS['default']['CONFIG'].copy()  # pylint: disable=invalid-name
# channels_config['hosts'] = [(REDIS_CONNECTION['host'], REDIS_CONNECTION['port'])]
#
# CHANNEL_LAYERS['default']['CONFIG'] = channels_config
# CHANNEL_LAYERS['default']['TEST_CONFIG'] = channels_config


# Testing

TEST_RUNNER = 'resolwe.test_helpers.test_runner.ResolweRunner'
TEST_PROCESS_REQUIRE_TAGS = True
TEST_PROCESS_PROFILE = False

# Logging

# In tests, log warning-level messages to the console, otherwise log info-level messages.
console_handler_level = (
    'WARNING' if 'test' in sys.argv else 'INFO'
)  # pylint: disable=invalid-name

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s - %(levelname)s - %(name)s[%(process)s]: %(message)s'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': console_handler_level,
            'formatter': 'standard',
        }
    },
    'loggers': {
        '': {'handlers': ['console'], 'level': 'DEBUG'},
        'raven': {'level': 'WARNING', 'handlers': ['console'], 'propagate': False},
        'elasticsearch': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'urllib3': {'handlers': ['console'], 'level': 'WARNING', 'propagate': False},
    },
}
