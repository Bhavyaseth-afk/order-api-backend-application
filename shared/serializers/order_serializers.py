"""
Order serializers for OrderAPI microservices.
"""
from rest_framework import serializers
from decimal import Decimal
from shared.models import Order
import logging

logger = logging.getLogger(__name__)

# Module-level constants for performance
SIDE_MAP = {1: 'buy', -1: 'sell'}
REVERSE_SIDE_MAP = {'buy': 1, 'sell': -1}


class OrderSerializer(serializers.ModelSerializer):
    """Serializer for Order model with side conversion."""
    
    side = serializers.SerializerMethodField()
    
    class Meta:
        model = Order
        fields = [
            'order_id', 'side', 'quantity', 'price', 'remaining_quantity',
            'traded_quantity', 'average_traded_price', 'status', 'is_active',
            'created_at', 'updated_at', 'user_id'
        ]
        read_only_fields = [
            'order_id', 'remaining_quantity', 'traded_quantity',
            'average_traded_price', 'status', 'is_active', 'created_at', 'updated_at'
        ]
    
    def get_side(self, obj):
        """Convert integer side to string for API response."""
        return SIDE_MAP.get(obj.side, 'unknown')
    
    def to_representation(self, instance):
        """Convert side values in response."""
        data = super().to_representation(instance)
        data['side'] = SIDE_MAP.get(instance.side, 'unknown')
        return data


class PlaceOrderSerializer(serializers.Serializer):
    """Serializer for placing new orders."""
    
    side = serializers.ChoiceField(choices=['buy', 'sell'])
    quantity = serializers.IntegerField(min_value=1)
    price = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=0.01)
    
    def validate_side(self, value):
        """Validate and convert side to integer."""
        if value not in REVERSE_SIDE_MAP:
            raise serializers.ValidationError("Side must be 'buy' or 'sell'")
        return REVERSE_SIDE_MAP[value]
    
    def validate_price(self, value):
        """Validate price format and value."""
        if value <= 0:
            raise serializers.ValidationError("Price must be positive")
        
        # Check if price is multiple of 0.01
        if value % Decimal('0.01') != 0:
            raise serializers.ValidationError("Price must be multiple of 0.01")
        
        return value
    
    def validate_quantity(self, value):
        """Validate quantity."""
        if value <= 0:
            raise serializers.ValidationError("Quantity must be positive")
        if value > 1000000:
            raise serializers.ValidationError("Quantity exceeds maximum allowed")
        return value


class ModifyOrderSerializer(serializers.Serializer):
    """Serializer for modifying existing orders."""
    
    order_id = serializers.UUIDField()
    price = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=0.01)
    
    def validate_price(self, value):
        """Validate price format and value."""
        if value <= 0:
            raise serializers.ValidationError("Price must be positive")
        
        # Check if price is multiple of 0.01
        if value % Decimal('0.01') != 0:
            raise serializers.ValidationError("Price must be multiple of 0.01")
        
        return value


class OrderResponseSerializer(serializers.Serializer):
    """Serializer for order API responses."""
    
    order_id = serializers.UUIDField()
    side = serializers.CharField()
    quantity = serializers.IntegerField()
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    remaining_quantity = serializers.IntegerField()
    traded_quantity = serializers.IntegerField()
    average_traded_price = serializers.DecimalField(max_digits=10, decimal_places=2)
    status = serializers.CharField()
    is_active = serializers.BooleanField()
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()


class OrderListResponseSerializer(serializers.Serializer):
    """Serializer for order list API responses."""
    
    orders = OrderResponseSerializer(many=True)
    count = serializers.IntegerField()
    page = serializers.IntegerField()
    total_pages = serializers.IntegerField()
