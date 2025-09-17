"""
Async Order Book implementation using hashmaps for O(1) operations.
"""
import asyncio
import logging
import threading
from decimal import Decimal
from typing import List, Dict, Optional

from asgiref.sync import sync_to_async
from shared.models import Order, Trade

logger = logging.getLogger(__name__)


class OrderBook:
    """High-performance async in-memory order book with O(1) operations."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Thread safety for concurrent access
        self._lock = threading.RLock()
        
        # Price level hashmaps: price -> list of orders
        self.bids: Dict[Decimal, List[Order]] = {}  # Buy orders
        self.asks: Dict[Decimal, List[Order]] = {}  # Sell orders
        
        # Order lookup: order_id -> (price, side, order)
        self.order_lookup: Dict[str, tuple] = {}
        
        # Best bid/ask for O(1) top-of-book access
        self.best_bid: Optional[Decimal] = None
        self.best_ask: Optional[Decimal] = None
        
        # Price level tracking for efficient best price updates
        self.bid_prices = set()
        self.ask_prices = set()
        
        # Performance metrics
        self.orders_processed = 0
        self.trades_created = 0
    
    async def add_order(self, order: Order) -> List[Trade]:
        """Add order to book and attempt matching. Returns list of trades."""
        trades = []
        
        try:
            with self._lock:
                self.logger.info(f"Processing order {order.order_id}: side={order.side}, price={order.price}, qty={order.remaining_quantity}")
                self.logger.info(f"Current order book state - Best bid: {self.best_bid}, Best ask: {self.best_ask}")
                
                # First, check for existing orders in database that could match
                await self._load_matching_orders(order)
                
                if order.side == 1:  # Buy order
                    trades = await self._match_buy_order(order)
                    if order.remaining_quantity > 0:
                        self._add_buy_order(order)
                        self.logger.info(f"Added buy order {order.order_id} to book at price {order.price}")
                else:  # Sell order  
                    trades = await self._match_sell_order(order)
                    if order.remaining_quantity > 0:
                        self._add_sell_order(order)
                        self.logger.info(f"Added sell order {order.order_id} to book at price {order.price}")
                
                # Update metrics
                self.orders_processed += 1
                self.trades_created += len(trades)
                
                self.logger.info(f"Order {order.order_id} processed, created {len(trades)} trades")
                self.logger.info(f"Updated order book state - Best bid: {self.best_bid}, Best ask: {self.best_ask}")
                return trades
                
        except Exception as e:
            self.logger.error(f"Error processing order {order.order_id}: {e}")
            return trades
    
    async def _load_matching_orders(self, new_order: Order):
        """Load existing orders from database that could potentially match with the new order."""
        try:
            if new_order.side == 1:  # Buy order - look for sell orders at or below this price
                existing_orders = await sync_to_async(list)(
                    Order.objects.filter(
                        side=-1,  # Sell orders
                        is_active=True,
                        status__in=['ACTIVE', 'PARTIALLY_FILLED'],
                        price__lte=new_order.price
                    ).exclude(order_id=new_order.order_id).order_by('price', 'created_at')
                )
            else:  # Sell order - look for buy orders at or above this price
                existing_orders = await sync_to_async(list)(
                    Order.objects.filter(
                        side=1,  # Buy orders
                        is_active=True,
                        status__in=['ACTIVE', 'PARTIALLY_FILLED'],
                        price__gte=new_order.price
                    ).exclude(order_id=new_order.order_id).order_by('-price', 'created_at')
                )
            
            self.logger.info(f"Found {len(existing_orders)} existing orders that could match with {new_order.order_id}")
            
            # Add these orders to the order book if they're not already there
            for order in existing_orders:
                order_key = str(order.order_id)
                if order_key not in self.order_lookup:
                    if order.side == 1:  # Buy order
                        self._add_buy_order(order)
                    else:  # Sell order
                        self._add_sell_order(order)
                    self.logger.info(f"Loaded existing order {order.order_id} into book")
                    
        except Exception as e:
            self.logger.error(f"Error loading matching orders: {e}")
    
    def _add_buy_order(self, order: Order):
        """Add buy order to bids."""
        price = order.price
        
        if price not in self.bids:
            self.bids[price] = []
            self.bid_prices.add(price)
        
        self.bids[price].append(order)
        self.order_lookup[str(order.order_id)] = (price, 1, order)
        
        if self.best_bid is None or price > self.best_bid:
            self.best_bid = price
    
    def _add_sell_order(self, order: Order):
        """Add sell order to asks."""
        price = order.price
        
        if price not in self.asks:
            self.asks[price] = []
            self.ask_prices.add(price)
        
        self.asks[price].append(order)
        self.order_lookup[str(order.order_id)] = (price, -1, order)
        
        if self.best_ask is None or price < self.best_ask:
            self.best_ask = price
    
    async def _match_buy_order(self, buy_order: Order) -> List[Trade]:
        """Match buy order against asks."""
        trades = []
        
        while buy_order.remaining_quantity > 0 and self.best_ask and buy_order.price >= self.best_ask:
            ask_orders = self.asks.get(self.best_ask, [])
            
            if not ask_orders:
                self._update_best_ask()
                continue
            
            sell_order = ask_orders[0]
            trade_quantity = min(buy_order.remaining_quantity, sell_order.remaining_quantity)
            
            # Create trade async
            trade = await sync_to_async(Trade.objects.create)(
                price=self.best_ask,
                quantity=trade_quantity,
                bid_order=buy_order,
                ask_order=sell_order
            )
            trades.append(trade)
            
            self.logger.info(f"Created trade: {trade_quantity} @ {self.best_ask} between {buy_order.order_id} and {sell_order.order_id}")
            
            # Update orders using the proper update_trade method (async)
            await sync_to_async(buy_order.update_trade)(trade_quantity, self.best_ask)
            await sync_to_async(sell_order.update_trade)(trade_quantity, self.best_ask)
            
            # Remove filled sell order
            if sell_order.remaining_quantity == 0:
                ask_orders.pop(0)
                del self.order_lookup[str(sell_order.order_id)]
                
                if not ask_orders:
                    del self.asks[self.best_ask]
                    self.ask_prices.discard(self.best_ask)
                    self._update_best_ask()
            
        return trades
    
    async def _match_sell_order(self, sell_order: Order) -> List[Trade]:
        """Match sell order against bids."""
        trades = []
        
        while sell_order.remaining_quantity > 0 and self.best_bid and sell_order.price <= self.best_bid:
            bid_orders = self.bids.get(self.best_bid, [])
            
            if not bid_orders:
                self._update_best_bid()
                continue
            
            buy_order = bid_orders[0]
            trade_quantity = min(sell_order.remaining_quantity, buy_order.remaining_quantity)
            
            # Create trade async
            trade = await sync_to_async(Trade.objects.create)(
                price=self.best_bid,
                quantity=trade_quantity,
                bid_order=buy_order,
                ask_order=sell_order
            )
            trades.append(trade)
            
            self.logger.info(f"Created trade: {trade_quantity} @ {self.best_bid} between {buy_order.order_id} and {sell_order.order_id}")
            
            # Update orders using the proper update_trade method (async)
            await sync_to_async(sell_order.update_trade)(trade_quantity, self.best_bid)
            await sync_to_async(buy_order.update_trade)(trade_quantity, self.best_bid)
            
            # Remove filled buy order
            if buy_order.remaining_quantity == 0:
                bid_orders.pop(0)
                del self.order_lookup[str(buy_order.order_id)]
                
                if not bid_orders:
                    del self.bids[self.best_bid]
                    self.bid_prices.discard(self.best_bid)
                    self._update_best_bid()
            
        return trades
    
    def _update_order_status(self, order: Order):
        """Update order status based on remaining quantity."""
        if order.remaining_quantity == 0:
            order.status = 'FILLED'
            order.is_active = False
        else:
            order.status = 'PARTIALLY_FILLED'
            order.is_active = True
    
    def _update_best_bid(self):
        """Update best bid price."""
        self.best_bid = max(self.bid_prices) if self.bid_prices else None
    
    def _update_best_ask(self):
        """Update best ask price."""
        self.best_ask = min(self.ask_prices) if self.ask_prices else None
    
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an order. Returns True if successful."""
        with self._lock:
            if order_id not in self.order_lookup:
                return False
                
            price, side, order = self.order_lookup[order_id]
            
            if side == 1:  # Buy order
                order_list = self.bids[price]
                order_list.remove(order)
                
                if not order_list:
                    del self.bids[price]
                    self.bid_prices.discard(price)
                    if price == self.best_bid:
                        self._update_best_bid()
            else:  # Sell order
                order_list = self.asks[price]
                order_list.remove(order)
                
                if not order_list:
                    del self.asks[price]
                    self.ask_prices.discard(price)
                    if price == self.best_ask:
                        self._update_best_ask()
            
            del self.order_lookup[order_id]
            order.status = 'CANCELLED'
            order.is_active = False
            await sync_to_async(order.save)()
            
            return True


# Global instance
order_book = OrderBook()
