"""
WebSocket Service Django settings.
"""
from shared.config.settings import *

# Service specific settings
SERVICE_NAME = 'websocket_service'
SERVICE_PORT = 8002

# Add service to installed apps (channels is already in shared settings)
INSTALLED_APPS += [
    'services.websocket_service',
]

# Channels configuration
ASGI_APPLICATION = 'websocket_service.asgi.application'
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [(REDIS_HOST, REDIS_PORT)],
        },
    },
}

# Service URLs
ROOT_URLCONF = 'services.websocket_service.urls'
