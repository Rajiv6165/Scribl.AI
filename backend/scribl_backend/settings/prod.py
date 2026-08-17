from .base import *

DEBUG = False

# Comma-separated list of allowed hosts
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=[])

CORS_ALLOW_CREDENTIALS = True
# Comma-separated list of allowed CORS origins
CORS_ALLOWED_ORIGINS = env.list('CORS_ALLOWED_ORIGINS', default=[])
CSRF_TRUSTED_ORIGINS = env.list('CSRF_TRUSTED_ORIGINS', default=[])

# Database Configuration (Uses DATABASE_URL e.g., postgres://user:pass@host:port/dbname)
DATABASES = {
    'default': env.db('DATABASE_URL')
}

# Redis Channel Layer Configuration (Uses REDIS_URL e.g., redis://host:port)
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [env('REDIS_URL')],
        },
    },
}

# Static files
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Basic error logging for production
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'WARNING',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': env('DJANGO_LOG_LEVEL', default='INFO'),
            'propagate': False,
        },
    },
}
