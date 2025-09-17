"""
WebSocket routing for WebSocket Service.
"""
from django.urls import path
from services.websocket_service import consumers

websocket_urlpatterns = [
    path('ws/trades/', consumers.TradeConsumer.as_asgi()),
    path('ws/orderbook/', consumers.OrderBookConsumer.as_asgi()),
]
