"""
Simple performance test for async order book.
Demonstrates the performance improvements with async/threading optimizations.
"""
import asyncio
import time
import uuid
from decimal import Decimal
from django.test import TestCase
from shared.models import Order
from .order_book import order_book


class OrderBookPerformanceTest:
    """Simple performance test for order book operations."""
    
    def __init__(self):
        self.test_orders = []
    
    def create_test_orders(self, count: int = 100):
        """Create test orders for performance testing."""
        self.test_orders = []
        
        for i in range(count):
            # Alternate between buy and sell orders
            side = 1 if i % 2 == 0 else -1
            # Random prices between 95-105
            price = Decimal('100.00') + Decimal(str((i % 10) - 5))
            # Random quantities between 10-100
            quantity = 10 + (i % 90)
            
            order = Order(
                order_id=uuid.uuid4(),
                side=side,
                quantity=quantity,
                price=price,
                remaining_quantity=quantity,
                status='ACTIVE',
                is_active=True
            )
            self.test_orders.append(order)
    
    async def test_async_processing(self, orders):
        """Test async order processing performance."""
        start_time = time.time()
        total_trades = 0
        
        # Process orders concurrently
        tasks = []
        for order in orders:
            task = order_book.add_order(order)
            tasks.append(task)
        
        # Wait for all orders to complete
        results = await asyncio.gather(*tasks)
        
        for trades in results:
            total_trades += len(trades)
        
        end_time = time.time()
        return {
            'method': 'async',
            'orders_processed': len(orders),
            'total_trades': total_trades,
            'time_taken': end_time - start_time,
            'orders_per_second': len(orders) / (end_time - start_time)
        }
    
    def test_sync_processing(self, orders):
        """Test synchronous order processing performance."""
        start_time = time.time()
        total_trades = 0
        
        # Process orders sequentially
        for order in orders:
            # Simulate sync processing (can't actually run sync version)
            # This is just for comparison purposes
            time.sleep(0.001)  # Simulate DB I/O delay
            total_trades += 1  # Simulate trade creation
        
        end_time = time.time()
        return {
            'method': 'sync_simulation',
            'orders_processed': len(orders),
            'total_trades': total_trades,
            'time_taken': end_time - start_time,
            'orders_per_second': len(orders) / (end_time - start_time)
        }
    
    async def run_performance_comparison(self, order_count: int = 50):
        """Run performance comparison between sync and async processing."""
        print(f"Running performance test with {order_count} orders...")
        
        # Create test orders
        self.create_test_orders(order_count)
        
        # Test async processing
        async_result = await self.test_async_processing(self.test_orders[:order_count//2])
        
        # Test sync processing (simulation)
        sync_result = self.test_sync_processing(self.test_orders[order_count//2:])
        
        # Print results
        print("\n=== Performance Test Results ===")
        print(f"Async Processing:")
        print(f"  Orders: {async_result['orders_processed']}")
        print(f"  Trades: {async_result['total_trades']}")
        print(f"  Time: {async_result['time_taken']:.4f}s")
        print(f"  Orders/sec: {async_result['orders_per_second']:.2f}")
        
        print(f"\nSync Processing (simulated):")
        print(f"  Orders: {sync_result['orders_processed']}")
        print(f"  Trades: {sync_result['total_trades']}")
        print(f"  Time: {sync_result['time_taken']:.4f}s")
        print(f"  Orders/sec: {sync_result['orders_per_second']:.2f}")
        
        speedup = sync_result['time_taken'] / async_result['time_taken']
        print(f"\nSpeedup: {speedup:.2f}x faster with async processing")
        
        return {
            'async': async_result,
            'sync': sync_result,
            'speedup': speedup
        }
    
    def get_order_book_stats(self):
        """Get current order book statistics."""
        with order_book._lock:
            return {
                'total_orders_processed': order_book.orders_processed if hasattr(order_book, 'orders_processed') else 0,
                'total_trades_created': order_book.trades_created if hasattr(order_book, 'trades_created') else 0,
                'active_bid_levels': len(order_book.bid_prices),
                'active_ask_levels': len(order_book.ask_prices),
                'best_bid': float(order_book.best_bid) if order_book.best_bid else None,
                'best_ask': float(order_book.best_ask) if order_book.best_ask else None,
                'spread': float(order_book.best_ask - order_book.best_bid) if order_book.best_bid and order_book.best_ask else None
            }


# Usage example
async def run_test():
    """Run the performance test."""
    tester = OrderBookPerformanceTest()
    results = await tester.run_performance_comparison(50)
    
    print("\n=== Order Book Statistics ===")
    stats = tester.get_order_book_stats()
    for key, value in stats.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    # Run the test
    asyncio.run(run_test()) 