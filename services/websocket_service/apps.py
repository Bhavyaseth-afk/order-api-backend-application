"""
WebSocket Service Django app configuration.
"""
from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)


class WebSocketServiceConfig(AppConfig):
    """WebSocket Service configuration."""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'services.websocket_service'
    verbose_name = 'WebSocket Service'
    
    def ready(self):
        """Initialize service when Django starts."""
        logger.info("WebSocket Service initialized")
