"""
Trade Service Django app configuration.
"""
from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)


class TradeServiceConfig(AppConfig):
    """Trade Service configuration."""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'services.trade_service'
    verbose_name = 'Trade Service'
    
    def ready(self):
        """Initialize service when Django starts."""
        logger.info("Trade Service initialized")
