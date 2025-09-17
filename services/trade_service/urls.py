"""
Trade Service URL configuration.
"""
from django.urls import include, path
from . import views

urlpatterns = [
    # Trade endpoints
    path('trades/', views.TradeListView.as_view(), name='trades'),
    path('trades/<uuid:trade_id>/', views.TradeDetailView.as_view(), name='trade_detail'),
    path('settle/<uuid:trade_id>/', views.TradeSettlementView.as_view(), name='settle_trade'),
    
    # Order endpoints
    path('orders/', views.OrdersListView.as_view(), name='orders'),
    
    # Order book endpoint
    path('orderbook/', views.OrderBookSnapshotView.as_view(), name='orderbook'),
    
    # Health check
    path('health/', include('health_check.urls')),
]
