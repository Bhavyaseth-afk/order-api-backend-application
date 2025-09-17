"""
Order Management Service Django app configuration.
"""
from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)


class OrderManagementConfig(AppConfig):
    """Order Management Service configuration."""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'services.order_management'
    verbose_name = 'Order Management Service'
    
    def ready(self):
        """Initialize service when Django starts."""
        logger.info("Order Management Service initialized")
