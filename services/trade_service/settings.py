"""
Trade Service Django settings.
"""
from shared.config.settings import *

# Service specific settings
SERVICE_NAME = 'trade_service'
SERVICE_PORT = 8001

# Add service to installed apps
INSTALLED_APPS += [
    'services.trade_service',
]

# Service URLs
ROOT_URLCONF = 'services.trade_service.urls'

# URL settings
APPEND_SLASH = True
