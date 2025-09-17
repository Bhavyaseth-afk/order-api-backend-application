"""
WebSocket consumers for real-time updates.
"""
import json
import asyncio
import logging
import aiohttp
from channels.generic.websocket import AsyncWebsocketConsumer

# Setup logging using standard Django logging
logger = logging.getLogger(__name__)


class TradeConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for trade notifications.
    """
    
    async def connect(self):
        """Handle WebSocket connection."""
        self.update_task = None
        await self.accept()
        
        # Start periodic updates for trades
        self.update_task = asyncio.create_task(self.send_periodic_trades())
        logger.info(f"Trade consumer connected: {self.channel_name}")
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        if self.update_task:
            self.update_task.cancel()
        logger.info(f"Trade consumer disconnected: {self.channel_name}")
    
    async def get_trades_data(self):
        """Fetch trades data from trade service."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get('http://localhost:8001/trades/') as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("trades", [])[:5]  # Get latest 5 trades
        except Exception as e:
            logger.error(f"Error fetching trades data: {e}")
            return []
    
    async def send_periodic_trades(self):
        """Send trade updates every second."""
        try:
            while True:
                # Get trades data from trade service
                trades_data = await self.get_trades_data()
                
                # Send to WebSocket client
                await self.send(text_data=json.dumps({
                    "trades": trades_data
                }))
                
                # Wait 1 second before next update
                await asyncio.sleep(1)
                
        except asyncio.CancelledError:
            logger.info("Trade periodic updates cancelled")
        except Exception as e:
            logger.error(f"Error in trade periodic updates: {e}")
    
    async def receive(self, text_data):
        """Handle messages from WebSocket client."""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'ping':
                await self.send(text_data=json.dumps({'type': 'pong'}))
            else:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': 'Unknown message type'
                }))
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON'
            }))


class OrderBookConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for order book snapshots.
    Sends order book snapshots with 5 levels of bid/ask depth every second.
    """
    
    async def connect(self):
        """Handle WebSocket connection."""
        self.update_task = None
        await self.accept()
        
        # Start periodic updates
        self.update_task = asyncio.create_task(self.send_periodic_updates())
        logger.info(f"Order book consumer connected: {self.channel_name}")
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        if self.update_task:
            self.update_task.cancel()
        logger.info(f"Order book consumer disconnected: {self.channel_name}")
    
    async def get_orderbook_data(self):
        """Fetch order book data from trade service."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get('http://localhost:8001/orderbook/') as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Convert buy_orders to bids format (price, quantity)
                        bids = []
                        for order in data.get("buy_orders", [])[:5]:
                            bids.append({
                                "price": order["price"],
                                "quantity": order["quantity"]
                            })
                        
                        # Convert sell_orders to asks format (price, quantity)
                        asks = []
                        for order in data.get("sell_orders", [])[:5]:
                            asks.append({
                                "price": order["price"],
                                "quantity": order["quantity"]
                            })
                        
                        return {
                            "bids": bids,
                            "asks": asks
                        }
        except Exception as e:
            logger.error(f"Error fetching orderbook data: {e}")
            # Fallback to empty data
            return {"bids": [], "asks": []}
    
    async def send_periodic_updates(self):
        """Send order book snapshots every second."""
        try:
            while True:
                # Get order book data from trade service
                orderbook_data = await self.get_orderbook_data()
                
                # Send to WebSocket client
                await self.send(text_data=json.dumps({
                    "bids": orderbook_data["bids"],
                    "asks": orderbook_data["asks"]
                }))
                
                # Wait 1 second before next update
                await asyncio.sleep(1)
                
        except asyncio.CancelledError:
            logger.info("Order book periodic updates cancelled")
        except Exception as e:
            logger.error(f"Error in order book periodic updates: {e}")
    
    async def receive(self, text_data):
        """Handle messages from WebSocket client."""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'ping':
                await self.send(text_data=json.dumps({'type': 'pong'}))
            else:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': 'Unknown message type'
                }))
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON'
            }))
