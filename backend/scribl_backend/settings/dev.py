from .base import *

DEBUG = True

ALLOWED_HOSTS = ['*']

CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

# Database Configuration
POSTGRES_DB = env('POSTGRES_DB', default=None)
POSTGRES_USER = env('POSTGRES_USER', default=None)
POSTGRES_PASSWORD = env('POSTGRES_PASSWORD', default=None)
POSTGRES_HOST = env('POSTGRES_HOST', default=None)
POSTGRES_PORT = env('POSTGRES_PORT', default='5432')

if POSTGRES_DB and POSTGRES_HOST:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': POSTGRES_DB,
            'USER': POSTGRES_USER,
            'PASSWORD': POSTGRES_PASSWORD,
            'HOST': POSTGRES_HOST,
            'PORT': POSTGRES_PORT,
        }
    }
else:
    # Local fallback for sqlite when testing outside Docker without PostgreSQL
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# Redis Channel Layer Configuration
REDIS_HOST = env('REDIS_HOST', default='redis')
REDIS_PORT = env('REDIS_PORT', default='6379')

if env('TESTING', default='0') == '1':
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels.layers.InMemoryChannelLayer',
        },
    }
else:
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels_redis.core.RedisChannelLayer',
            'CONFIG': {
                "hosts": [(REDIS_HOST, int(REDIS_PORT))],
            },
        },
    }
