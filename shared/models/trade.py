"""
Trade model for the OrderAPI microservices system.
"""
from django.db import models
from django.utils import timezone
import uuid
import logging

logger = logging.getLogger(__name__)


class Trade(models.Model):
    """
    Model representing a trade that occurred between two orders.
    """
    # Primary key
    trade_id = models.UUIDField(
        primary_key=True, 
        default=uuid.uuid4, 
        editable=False,
        help_text="Unique identifier for the trade"
    )
    
    # Trade details
    price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        help_text="Execution price"
    )
    quantity = models.PositiveIntegerField(
        help_text="Quantity traded"
    )
    
    # Order references
    bid_order = models.ForeignKey(
        'Order', 
        on_delete=models.CASCADE, 
        related_name='bid_trades',
        help_text="Buy order that participated in the trade"
    )
    ask_order = models.ForeignKey(
        'Order', 
        on_delete=models.CASCADE, 
        related_name='ask_trades',
        help_text="Sell order that participated in the trade"
    )
    
    # Timestamps
    execution_timestamp = models.DateTimeField(
        default=timezone.now,
        help_text="When the trade was executed"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Settlement status
    is_settled = models.BooleanField(
        default=False,
        help_text="Whether the trade has been settled"
    )
    settlement_timestamp = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="When the trade was settled"
    )
    
    class Meta:
        ordering = ['-execution_timestamp']
        indexes = [
            models.Index(fields=['execution_timestamp']),
            models.Index(fields=['bid_order']),
            models.Index(fields=['ask_order']),
            models.Index(fields=['is_settled']),
        ]
    
    def __str__(self):
        return f"Trade {self.trade_id}: {self.quantity} @ {self.price}"
    
    def save(self, *args, **kwargs):
        """Override save to add logging."""
        logger.info(f"Saving trade {self.trade_id}: {self.quantity} @ {self.price}")
        super().save(*args, **kwargs)
    
    def mark_as_settled(self):
        """Mark trade as settled."""
        self.is_settled = True
        self.settlement_timestamp = timezone.now()
        logger.info(f"Trade {self.trade_id} marked as settled")
        self.save()
    
    def to_dict(self):
        """Convert trade to dictionary for API responses."""
        return {
            'trade_id': str(self.trade_id),
            'execution_timestamp': self.execution_timestamp.isoformat(),
            'price': float(self.price),
            'quantity': self.quantity,
            'bid_order_id': str(self.bid_order.order_id),
            'ask_order_id': str(self.ask_order.order_id),
            'is_settled': self.is_settled,
            'settlement_timestamp': self.settlement_timestamp.isoformat() if self.settlement_timestamp else None
        }
