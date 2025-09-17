"""
Order model for the OrderAPI microservices system.
"""
from django.db import models
from django.utils import timezone
import uuid
import logging

logger = logging.getLogger(__name__)


class Order(models.Model):
    """
    Model representing an order in the order book.
    Optimized for high-frequency trading operations.
    """
    SIDE_CHOICES = [
        (1, 'Buy'),
        (-1, 'Sell'),
    ]
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('ACTIVE', 'Active'),
        ('PARTIALLY_FILLED', 'Partially Filled'),
        ('FILLED', 'Filled'),
        ('CANCELLED', 'Cancelled'),
        ('REJECTED', 'Rejected'),
    ]
    
    # Primary key
    order_id = models.UUIDField(
        primary_key=True, 
        default=uuid.uuid4, 
        editable=False,
        help_text="Unique identifier for the order"
    )
    
    # Order details
    side = models.IntegerField(
        choices=SIDE_CHOICES, 
        help_text="1 for buy, -1 for sell"
    )
    quantity = models.PositiveIntegerField(
        help_text="Total quantity to buy/sell"
    )
    price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        help_text="Price per unit"
    )
    
    # Execution tracking
    remaining_quantity = models.PositiveIntegerField(
        help_text="Remaining quantity after partial fills"
    )
    traded_quantity = models.PositiveIntegerField(
        default=0, 
        help_text="Quantity that has been traded"
    )
    average_traded_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0, 
        help_text="Average price of traded quantity"
    )
    
    # Status and lifecycle
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='PENDING',
        help_text="Current status of the order"
    )
    is_active = models.BooleanField(
        default=True, 
        help_text="Whether the order is still active in the order book"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # User association
    user_id = models.UUIDField(
        null=True, 
        blank=True,
        help_text="User who placed the order"
    )
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['side', 'price', 'created_at']),
            models.Index(fields=['is_active']),
            models.Index(fields=['status']),
            models.Index(fields=['user_id']),
        ]
    
    def __str__(self):
        return f"Order {self.order_id}: {self.get_side_display()} {self.remaining_quantity} @ {self.price}"
    
    def save(self, *args, **kwargs):
        """Override save to add logging and validation."""
        logger.info(f"Saving order {self.order_id} with status {self.status}")
        super().save(*args, **kwargs)
    
    def mark_as_filled(self):
        """Mark order as completely filled."""
        self.status = 'FILLED'
        self.is_active = False
        self.remaining_quantity = 0
        self.updated_at = timezone.now()
        logger.info(f"Order {self.order_id} marked as filled")
        self.save()
    
    def mark_as_cancelled(self):
        """Mark order as cancelled."""
        self.status = 'CANCELLED'
        self.is_active = False
        self.remaining_quantity = 0
        self.updated_at = timezone.now()
        logger.info(f"Order {self.order_id} marked as cancelled")
        self.save()
    
    def update_trade(self, trade_quantity, trade_price):
        """Update order with new trade information."""
        if trade_quantity > self.remaining_quantity:
            raise ValueError("Trade quantity exceeds remaining quantity")
        
        # Update quantities
        self.remaining_quantity -= trade_quantity
        self.traded_quantity += trade_quantity
        
        # Calculate new average price
        if self.traded_quantity > 0:
            total_value = (self.average_traded_price * (self.traded_quantity - trade_quantity) + 
                          trade_price * trade_quantity)
            self.average_traded_price = total_value / self.traded_quantity
        
        # Update status
        if self.remaining_quantity == 0:
            self.mark_as_filled()
        elif self.traded_quantity > 0:
            self.status = 'PARTIALLY_FILLED'
        
        self.updated_at = timezone.now()
        logger.info(f"Order {self.order_id} updated with trade: {trade_quantity} @ {trade_price}")
        self.save()
