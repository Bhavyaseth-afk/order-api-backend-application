"""
WebSocket Service URL configuration.
"""
from django.urls import path, include

urlpatterns = [
    path('health/', include('health_check.urls')),
    # WebSocket routing is handled in routing.py
]
