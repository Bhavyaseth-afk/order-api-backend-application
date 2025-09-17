"""
WebSocket Service API views.
"""
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

# Setup logging
logger = logging.getLogger(__name__)


class HealthCheckView(APIView):
    """
    Health check endpoint.
    
    GET /health/
    """    
    def get(self, request):
        try:
            logger.info("WebSocket service health check requested")
            return Response({
                'status': 'healthy',
                'service': 'websocket_service',
                'websocket_endpoints': [
                    'ws://localhost:8004/ws/trades/',
                    'ws://localhost:8004/ws/orderbook/'
                ]
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return Response({
                'status': 'unhealthy',
                'service': 'websocket_service',
                'error': str(e)
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
