"""
Order Management Service Django settings.
"""
from shared.config.settings import *

# Service specific settings
SERVICE_NAME = 'order_management'
SERVICE_PORT = 8000

# Add service to installed apps
INSTALLED_APPS += [
    'services.order_management',
]

# Database routing (if needed)
DATABASE_ROUTERS = []

# Service URLs
ROOT_URLCONF = 'services.order_management.urls'

# URL settings
APPEND_SLASH = True
