"""
Order Management Service API views.
Handles order CRUD operations and matching engine with async support.
"""
import asyncio
import logging
import threading
from rest_framework import status
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework.decorators import action
from asgiref.sync import async_to_sync


from shared.models import Order
from shared.serializers import (
    OrderSerializer, PlaceOrderSerializer, ModifyOrderSerializer,
    OrderResponseSerializer
)
from shared.utils import validate_order_data
from .order_book import order_book

# Setup logging
logger = logging.getLogger(__name__)


def _process_order_in_background(order):
    """Background thread function to process order in order book."""
    try:
        trades = async_to_sync(order_book.add_order)(order)
        logger.info(f"Background processing completed for order {order.order_id}, created {len(trades)} trades")
    except Exception as e:
        logger.error(f"Background processing failed for order {order.order_id}: {e}")


class OrderViewSet(ModelViewSet):
    """
    Handles order CRUD operations and matching.
    """
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    
    def create(self, request):
        """
        Place a new order.
        
        POST /orders/
        Body: {
            "side": "buy" | "sell",
            "quantity": int,
            "price": float,
            "user_id": "uuid"
        }
        """        
        try:
            # Validate input data
            serializer = PlaceOrderSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            # Additional validation
            is_valid, error_msg = validate_order_data(serializer.validated_data)
            if not is_valid:
                return Response({'error': error_msg}, status=status.HTTP_400_BAD_REQUEST)
            
            # Create order as ACTIVE
            order_data = serializer.validated_data.copy()
            order_data['remaining_quantity'] = order_data['quantity']
            order_data['status'] = 'ACTIVE'
            
            order = Order.objects.create(**order_data)
            logger.info(f"Order {order.order_id} created as ACTIVE")
            
            # Process order in background thread
            thread = threading.Thread(target=_process_order_in_background, args=(order,))
            thread.daemon = True
            thread.start()
            
            # Return immediate response with ACTIVE status
            return Response({
                'order_id': str(order.order_id),
                'message': 'Order placed successfully and is being processed',
                'status': order.status,
                'side': 'buy' if order.side == 1 else 'sell',
                'quantity': order.quantity,
                'remaining_quantity': order.remaining_quantity,
                'traded_quantity': order.traded_quantity,
                'price': float(order.price)
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Error placing order: {e}")
            return Response({'error': 'Failed to place order'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

    
    def update(self, request, pk=None):
        """
        Modify an existing order.
        
        PUT /orders/{order_id}/
        Body: {
            "price": float
        }
        """
        try:
            # Get order
            try:
                order = Order.objects.get(order_id=pk)
            except Order.DoesNotExist:
                return Response(
                    {'error': 'Order not found'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Check if order can be modified
            if not order.is_active or order.status in ['FILLED', 'CANCELLED']:
                return Response(
                    {'error': 'Order cannot be modified'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validate new price
            serializer = ModifyOrderSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            new_price = serializer.validated_data['price']
            
            # Update order with new price and set as ACTIVE
            order.price = new_price
            order.status = 'ACTIVE'
            order.is_active = True
            order.save()
            
            # Process modified order in background thread
            def _process_modified_order_in_background():
                try:
                    # Cancel existing order from book and re-add with new price
                    async_to_sync(order_book.cancel_order)(str(order.order_id))
                    trades = async_to_sync(order_book.add_order)(order)
                    logger.info(f"Background processing completed for modified order {order.order_id}, created {len(trades)} trades")
                except Exception as e:
                    logger.error(f"Background processing failed for modified order {order.order_id}: {e}")
            
            thread = threading.Thread(target=_process_modified_order_in_background)
            thread.daemon = True
            thread.start()
            
            # Return immediate response
            return Response({
                'message': 'Order modified successfully and is being processed',
                'order_id': str(order.order_id),
                'new_price': float(new_price),
                'status': order.status
            })
            
        except Exception as e:
            logger.error(f"Error modifying order: {e}")
            return Response(
                {'error': 'Failed to modify order'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def destroy(self, request, pk=None):
        """
        Cancel an existing order.
        
        DELETE /orders/{order_id}/
        """
        try:
            # Get order
            try:
                order = Order.objects.get(order_id=pk)
            except Order.DoesNotExist:
                return Response(
                    {'error': 'Order not found'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Check if order can be cancelled
            if not order.is_active or order.status in ['FILLED', 'CANCELLED']:
                return Response(
                    {'error': 'Order cannot be cancelled'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Cancel order in order book and database
            success = async_to_sync(order_book.cancel_order)(str(order.order_id))
            
            if success:
                return Response({
                    'message': 'Order cancelled successfully',
                    'order_id': str(order.order_id)
                })
            else:
                # Order not in book, just update database
                order.status = 'CANCELLED'
                order.is_active = False
                order.save()
                return Response({
                    'message': 'Order cancelled successfully',
                    'order_id': str(order.order_id)
                })
                
        except Exception as e:
            logger.error(f"Error cancelling order: {e}")
            return Response(
                {'error': 'Failed to cancel order'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def retrieve(self, request, pk=None):
        """
        Get order details.
        
        GET /orders/{order_id}/
        """        
        try:
            # Get from database
            try:
                order = Order.objects.get(order_id=pk)
            except Order.DoesNotExist:
                return Response(
                    {'error': 'Order not found'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Return order data
            order_data = OrderResponseSerializer(order).data
            return Response(order_data)
            
        except Exception as e:
            logger.error(f"Error retrieving order: {e}")
            return Response(
                {'error': 'Failed to retrieve order'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def list(self, request):
        """
        List orders with optional filtering and pagination.
        
        GET /orders/?status=ACTIVE&side=buy&user_id=uuid&page=1
        """
        try:
            queryset = Order.objects.all()
            
            # Apply filters
            status_filter = request.query_params.get('status')
            if status_filter:
                queryset = queryset.filter(status=status_filter)
            
            side_filter = request.query_params.get('side')
            if side_filter:
                side_value = 1 if side_filter.lower() == 'buy' else -1
                queryset = queryset.filter(side=side_value)
            
            user_id = request.query_params.get('user_id')
            if user_id:
                queryset = queryset.filter(user_id=user_id)
            
            # Order by creation time (newest first)
            queryset = queryset.order_by('-created_at')
            
            # Apply pagination
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = OrderResponseSerializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            
            # Fallback for when pagination is disabled
            serializer = OrderResponseSerializer(queryset, many=True)
            return Response(serializer.data)
            
        except Exception as e:
            logger.error(f"Error listing orders: {e}")
            return Response(
                {'error': 'Failed to list orders'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
