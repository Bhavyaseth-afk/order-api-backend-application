"""
User model for the OrderAPI microservices system.
"""
from django.contrib.auth.models import AbstractUser
from django.db import models
import uuid
import logging

logger = logging.getLogger(__name__)


class User(AbstractUser):
    """
    Extended user model for the OrderAPI system.
    """
    # Primary key
    user_id = models.UUIDField(
        primary_key=True, 
        default=uuid.uuid4, 
        editable=False,
        help_text="Unique identifier for the user"
    )
    
    # Additional fields
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Trading specific fields
    trading_enabled = models.BooleanField(
        default=True,
        help_text="Whether the user can place orders"
    )
    max_order_value = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=1000000.00,
        help_text="Maximum value for a single order"
    )
    
    # Fix reverse accessor conflicts
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to.',
        related_name='custom_user_set',
        related_query_name='custom_user',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name='custom_user_set',
        related_query_name='custom_user',
    )
    
    class Meta:
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['is_active']),
            models.Index(fields=['trading_enabled']),
        ]
    
    def __str__(self):
        return f"User {self.user_id}: {self.email}"
    
    def save(self, *args, **kwargs):
        """Override save to add logging."""
        logger.info(f"Saving user {self.user_id}: {self.email}")
        super().save(*args, **kwargs)
    
    def can_place_order(self, order_value):
        """Check if user can place an order with given value."""
        return (
            self.is_active and 
            self.trading_enabled and 
            order_value <= self.max_order_value
        )
