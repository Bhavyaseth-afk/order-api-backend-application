"""
Trade serializers for OrderAPI microservices.
"""
from rest_framework import serializers
from shared.models import Trade
import logging

logger = logging.getLogger(__name__)


class TradeSerializer(serializers.ModelSerializer):
    """Serializer for Trade model."""
    
    class Meta:
        model = Trade
        fields = [
            'trade_id', 'price', 'quantity', 'bid_order', 'ask_order',
            'execution_timestamp', 'is_settled', 'settlement_timestamp'
        ]
        read_only_fields = [
            'trade_id', 'execution_timestamp', 'is_settled', 'settlement_timestamp'
        ]


class TradeResponseSerializer(serializers.Serializer):
    """Serializer for trade API responses."""
    
    trade_id = serializers.UUIDField()
    execution_timestamp = serializers.DateTimeField()
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    quantity = serializers.IntegerField()
    bid_order_id = serializers.UUIDField()
    ask_order_id = serializers.UUIDField()
    is_settled = serializers.BooleanField()
    settlement_timestamp = serializers.DateTimeField(allow_null=True)


class TradeListResponseSerializer(serializers.Serializer):
    """Serializer for trade list API responses."""
    
    trades = TradeResponseSerializer(many=True)
    count = serializers.IntegerField()
    page = serializers.IntegerField()
    total_pages = serializers.IntegerField()


class OrderBookSnapshotSerializer(serializers.Serializer):
    """Serializer for order book snapshot responses."""
    
    buy_orders = serializers.ListField(
        child=serializers.DictField()
    )
    sell_orders = serializers.ListField(
        child=serializers.DictField()
    )
    timestamp = serializers.DateTimeField()
    depth = serializers.IntegerField()
