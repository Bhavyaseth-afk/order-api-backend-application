"""
Trade Service API views.
Handles trade operations and order book snapshots.
"""
import json
import logging
from decimal import Decimal
from django.utils import timezone
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.core.paginator import Paginator

from shared.models import Order, Trade
from shared.serializers import TradeSerializer, OrderBookSnapshotSerializer
from shared.utils import get_redis_client

# Setup logging
logger = logging.getLogger(__name__)

# Redis client
redis_client = get_redis_client()


class TradeListView(APIView):
    """
    Get all trades with pagination.
    
    GET /trades/?page=1&page_size=20
    """
    
    def get(self, request):
        try:
            page = int(request.GET.get('page', 1))
            page_size = int(request.GET.get('page_size', 20))
            
            if page < 1:
                page = 1
            if page_size < 1 or page_size > 100:
                page_size = 20
            
            # Get trades with pagination
            trades = Trade.objects.all().order_by('-created_at')
            paginator = Paginator(trades, page_size)
            
            try:
                page_obj = paginator.page(page)
            except:
                page_obj = paginator.page(1)
            
            # Serialize trades
            serializer = TradeSerializer(page_obj.object_list, many=True)
            
            return Response({
                'trades': serializer.data,
                'pagination': {
                    'page': page,
                    'page_size': page_size,
                    'total_pages': paginator.num_pages,
                    'total_count': paginator.count,
                    'has_next': page_obj.has_next(),
                    'has_previous': page_obj.has_previous(),
                }
            })
            
        except Exception as e:
            logger.error(f"Error getting trades: {e}")
            return Response(
                {'error': 'Failed to get trades'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TradeDetailView(APIView):
    """
    Get trade details.
    
    GET /trades/{trade_id}/
    """
    
    def get(self, request, trade_id):
        try:
            try:
                trade = Trade.objects.get(trade_id=trade_id)
            except Trade.DoesNotExist:
                return Response(
                    {'error': 'Trade not found'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            serializer = TradeSerializer(trade)
            return Response(serializer.data)
            
        except Exception as e:
            logger.error(f"Error getting trade: {e}")
            return Response(
                {'error': 'Failed to get trade'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TradeSettlementView(APIView):
    """
    Settle a trade.
    
    POST /trades/{trade_id}/settle/
    """
    
    def post(self, request, trade_id):
        try:
            try:
                trade = Trade.objects.get(trade_id=trade_id)
            except Trade.DoesNotExist:
                return Response(
                    {'error': 'Trade not found'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Check if trade is already settled
            if trade.is_settled:
                return Response(
                    {'error': 'Trade already settled'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Settle the trade
            trade.is_settled = True
            trade.settled_at = timezone.now()
            trade.save()
            
            logger.info(f"Trade {trade_id} settled successfully")
            
            # Return updated trade
            serializer = TradeSerializer(trade)
            return Response({
                'message': 'Trade settled successfully',
                'trade': serializer.data
            })
            
        except Exception as e:
            logger.error(f"Error settling trade: {e}")
            return Response(
                {'error': 'Failed to settle trade'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class OrderBookSnapshotView(APIView):
    """
    Get order book snapshot from database.
    
    GET /orderbook/?depth=5
    """
    
    def get(self, request):
        try:
            depth = int(request.GET.get('depth', 5))
            if depth < 1 or depth > 20:
                return Response(
                    {'error': 'Depth must be between 1 and 20'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            logger.info(f"Order book snapshot requested with depth {depth}")
            
            # Get active orders from database
            buy_orders = Order.objects.filter(
                side=1,  # Buy
                status__in=['ACTIVE', 'PARTIALLY_FILLED'],
                remaining_quantity__gt=0
            ).order_by('-price', 'created_at')[:depth]
            
            sell_orders = Order.objects.filter(
                side=-1,  # Sell
                status__in=['ACTIVE', 'PARTIALLY_FILLED'],
                remaining_quantity__gt=0
            ).order_by('price', 'created_at')[:depth]
            
            # Prepare order book data
            orderbook_data = {
                'buy_orders': [],
                'sell_orders': [],
                'timestamp': timezone.now().isoformat(),
                'depth': depth,
                'total_buy_orders': buy_orders.count(),
                'total_sell_orders': sell_orders.count()
            }
            
            # Format buy orders (highest price first)
            for order in buy_orders:
                orderbook_data['buy_orders'].append({
                    'order_id': str(order.order_id),
                    'price': float(order.price),
                    'quantity': order.remaining_quantity,
                    'total_quantity': order.quantity,
                    'traded_quantity': order.traded_quantity,
                    'status': order.status,
                    'created_at': order.created_at.isoformat(),
                    'user_id': str(order.user_id) if order.user_id else None
                })
            
            # Format sell orders (lowest price first)
            for order in sell_orders:
                orderbook_data['sell_orders'].append({
                    'order_id': str(order.order_id),
                    'price': float(order.price),
                    'quantity': order.remaining_quantity,
                    'total_quantity': order.quantity,
                    'traded_quantity': order.traded_quantity,
                    'status': order.status,
                    'created_at': order.created_at.isoformat(),
                    'user_id': str(order.user_id) if order.user_id else None
                })
            
            logger.info(f"Order book snapshot generated with {len(orderbook_data['buy_orders'])} buy orders and {len(orderbook_data['sell_orders'])} sell orders")
            return Response(orderbook_data)
            
        except Exception as e:
            logger.error(f"Error getting order book snapshot: {e}")
            return Response(
                {'error': 'Failed to get order book snapshot'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class OrdersListView(APIView):
    """
    Get all orders with pagination.
    
    GET /orders/?page=1&page_size=20&status=ACTIVE
    """
    
    def get(self, request):
        try:
            page = int(request.GET.get('page', 1))
            page_size = int(request.GET.get('page_size', 20))
            status_filter = request.GET.get('status')
            side_filter = request.GET.get('side')
            user_id = request.GET.get('user_id')
            
            if page < 1:
                page = 1
            if page_size < 1 or page_size > 100:
                page_size = 20
            
            # Build query
            orders = Order.objects.all()
            
            if status_filter:
                orders = orders.filter(status=status_filter)
            
            if side_filter:
                side_value = 1 if side_filter.lower() == 'buy' else -1
                orders = orders.filter(side=side_value)
            
            if user_id:
                orders = orders.filter(user_id=user_id)
            
            # Order by creation time (newest first)
            orders = orders.order_by('-created_at')
            
            # Paginate
            paginator = Paginator(orders, page_size)
            
            try:
                page_obj = paginator.page(page)
            except:
                page_obj = paginator.page(1)
            
            # Serialize orders
            orders_data = []
            for order in page_obj.object_list:
                orders_data.append({
                    'order_id': str(order.order_id),
                    'side': 'buy' if order.side == 1 else 'sell',
                    'price': float(order.price),
                    'quantity': order.quantity,
                    'remaining_quantity': order.remaining_quantity,
                    'traded_quantity': order.traded_quantity,
                    'average_traded_price': float(order.average_traded_price),
                    'status': order.status,
                    'is_active': order.is_active,
                    'created_at': order.created_at.isoformat(),
                    'updated_at': order.updated_at.isoformat(),
                    'user_id': str(order.user_id) if order.user_id else None
                })
            
            return Response({
                'orders': orders_data,
                'pagination': {
                    'page': page,
                    'page_size': page_size,
                    'total_pages': paginator.num_pages,
                    'total_count': paginator.count,
                    'has_next': page_obj.has_next(),
                    'has_previous': page_obj.has_previous(),
                }
            })
            
        except Exception as e:
            logger.error(f"Error getting orders: {e}")
            return Response(
                {'error': 'Failed to get orders'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
