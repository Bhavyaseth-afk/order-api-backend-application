"""
Validation utilities for OrderAPI microservices.
"""
from decimal import Decimal, ROUND_DOWN
import logging

logger = logging.getLogger(__name__)


def validate_price(price: float) -> bool:
    """
    Validate price according to business rules.
    
    Args:
        price (float): Price to validate
    
    Returns:
        bool: True if valid, False otherwise
    """
    try:
        price_decimal = Decimal(str(price))
        
        # Check if price is positive
        if price_decimal <= 0:
            logger.warning(f"Invalid price: {price} - must be positive")
            return False
        
        # Check if price is multiple of 0.01
        if price_decimal % Decimal('0.01') != 0:
            logger.warning(f"Invalid price: {price} - must be multiple of 0.01")
            return False
        
        # Check if price is within reasonable range
        if price_decimal > Decimal('999999.99'):
            logger.warning(f"Invalid price: {price} - exceeds maximum value")
            return False
        
        return True
        
    except (ValueError, TypeError) as e:
        logger.error(f"Price validation error: {e}")
        return False


def validate_quantity(quantity: int) -> bool:
    """
    Validate quantity according to business rules.
    
    Args:
        quantity (int): Quantity to validate
    
    Returns:
        bool: True if valid, False otherwise
    """
    try:
        # Check if quantity is positive integer
        if not isinstance(quantity, int) or quantity <= 0:
            logger.warning(f"Invalid quantity: {quantity} - must be positive integer")
            return False
        
        # Check if quantity is within reasonable range
        if quantity > 1000000:
            logger.warning(f"Invalid quantity: {quantity} - exceeds maximum value")
            return False
        
        return True
        
    except (ValueError, TypeError) as e:
        logger.error(f"Quantity validation error: {e}")
        return False


def validate_side(side: int) -> bool:
    """
    Validate order side.
    
    Args:
        side (int): Side to validate (1 for buy, -1 for sell)
    
    Returns:
        bool: True if valid, False otherwise
    """
    if side not in [1, -1]:
        logger.warning(f"Invalid side: {side} - must be 1 (buy) or -1 (sell)")
        return False
    return True


def validate_order_data(data: dict) -> tuple[bool, str]:
    """
    Validate complete order data.
    
    Args:
        data (dict): Order data to validate
    
    Returns:
        tuple: (is_valid, error_message)
    """
    try:
        # Check required fields
        required_fields = ['side', 'quantity', 'price']
        for field in required_fields:
            if field not in data:
                return False, f"Missing required field: {field}"
        
        # Validate side
        if not validate_side(data['side']):
            return False, "Invalid side: must be 1 (buy) or -1 (sell)"
        
        # Validate quantity
        if not validate_quantity(data['quantity']):
            return False, "Invalid quantity: must be positive integer"
        
        # Validate price
        if not validate_price(data['price']):
            return False, "Invalid price: must be positive and multiple of 0.01"
        
        return True, ""
        
    except Exception as e:
        logger.error(f"Order validation error: {e}")
        return False, f"Validation error: {str(e)}"


def normalize_price(price: float) -> Decimal:
    """
    Normalize price to 2 decimal places.
    
    Args:
        price (float): Price to normalize
    
    Returns:
        Decimal: Normalized price
    """
    return Decimal(str(price)).quantize(Decimal('0.01'), rounding=ROUND_DOWN)
