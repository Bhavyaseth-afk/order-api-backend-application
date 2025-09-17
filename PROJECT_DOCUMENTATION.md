
## 🎯 Project Overview

The **Order API Microservices** is a high-performance trading system built with Django and Django REST Framework. It implements a complete order matching engine with real-time WebSocket updates, designed for financial trading applications.

### Key Features
- **High-Performance Order Matching**: O(1) order book operations using hashmaps
- **Real-time Updates**: WebSocket connections for live order book and trade data
- **Microservices Architecture**: Three specialized services for different concerns
- **Async Processing**: Background order processing for immediate API responses
- **Data Persistence**: PostgreSQL/SQLite with Redis for caching
- **Trade Settlement**: Complete trade lifecycle management
- **Docker Support**: Full containerization with Docker Compose

---

### Shared Components
- **Models**: Common data models (Order, Trade, User)
- **Serializers**: API serialization logic
- **Utilities**: Validation functions, Redis client
- **Configuration**: Shared settings and database configuration

---

## 🔧 Services

### 1. Order Management Service (Port 8000)
**Primary responsibility**: Core order processing and matching engine

**Key Components**:
- **Order ViewSet**: Full CRUD operations for orders
- **Background Processing**: Async order matching using threading
- **Validation**: Business rule validation for orders

**Features**:
- Place new orders with immediate response
- Modify existing order prices
- Cancel active orders
- List and filter orders with pagination
- Real-time order matching and trade execution

### 2. Trade Service (Port 8001)
**Primary responsibility**: Trade data management and order book snapshots

**Key Components**:
- **Trade Management**: Trade listing and details
- **Settlement**: Trade settlement operations
- **Order Book Snapshots**: Current market depth data
- **Order Listing**: Alternative order viewing endpoint

**Features**:
- View all trades with pagination
- Get individual trade details
- Settle trades for completion
- Get order book depth snapshots
- Filter orders by various criteria

### 3. WebSocket Service (Port 8002)
**Primary responsibility**: Real-time data streaming

**Key Components**:
- **Trade Consumer**: Live trade feed updates
- **Order Book Consumer**: Real-time order book snapshots
- **Channel Routing**: WebSocket URL routing

**Features**:
- Real-time trade notifications (1-second intervals)
- Live order book updates with bid/ask data
- WebSocket connection management
- Ping/pong heartbeat support

---

## 📊 Data Models

### Order Model
```python
class Order(models.Model):
    order_id = UUIDField(primary_key=True)           # Unique identifier
    side = IntegerField(choices=[(1, 'Buy'), (-1, 'Sell')])  # Order direction
    quantity = PositiveIntegerField()                # Total quantity
    price = DecimalField(max_digits=10, decimal_places=2)  # Price per unit
    remaining_quantity = PositiveIntegerField()      # Unfilled quantity
    traded_quantity = PositiveIntegerField()         # Filled quantity
    average_traded_price = DecimalField()            # Average execution price
    status = CharField(max_length=20)                # Order status
    is_active = BooleanField()                       # Active in order book
    user_id = UUIDField(null=True)                   # User association
    created_at = DateTimeField()                     # Creation timestamp
    updated_at = DateTimeField()                     # Last update
```

**Order Statuses**:
- `PENDING`: Just created, not yet processed
- `ACTIVE`: In the order book, awaiting matching
- `PARTIALLY_FILLED`: Some quantity has been traded
- `FILLED`: Completely executed
- `CANCELLED`: Cancelled by user
- `REJECTED`: Rejected due to validation errors

### Trade Model
```python
class Trade(models.Model):
    trade_id = UUIDField(primary_key=True)           # Unique identifier
    price = DecimalField(max_digits=10, decimal_places=2)  # Execution price
    quantity = PositiveIntegerField()                # Traded quantity
    bid_order = ForeignKey(Order)                    # Buy order reference
    ask_order = ForeignKey(Order)                    # Sell order reference
    execution_timestamp = DateTimeField()            # Execution time
    is_settled = BooleanField()                      # Settlement status
    settlement_timestamp = DateTimeField()           # Settlement time
```

---

## 🔌 API Endpoints

### Order Management Service (http://localhost:8000)

#### Orders
- **POST /orders/** - Place new order
- **GET /orders/** - List orders with filtering
- **GET /orders/{order_id}/** - Get order details
- **PUT /orders/{order_id}/** - Modify order price
- **DELETE /orders/{order_id}/** - Cancel order

### Trade Service (http://localhost:8001)

#### Trades
- **GET /trades/** - List all trades
- **GET /trades/{trade_id}/** - Get trade details
- **POST /trades/{trade_id}/settle/** - Settle trade

#### Order Book
- **GET /orderbook/** - Get order book snapshot
- **GET /orders/** - Alternative order listing

---

## 🌐 WebSocket Connections

### Trade Feed (ws://localhost:8002/ws/trades/)
Provides real-time trade updates every second.

**Message Format**:
```json
{
    "trades": [
        {
            "trade_id": "uuid",
            "price": 100.50,
            "quantity": 10,
            "execution_timestamp": "2024-01-01T12:00:00Z",
            "bid_order_id": "uuid",
            "ask_order_id": "uuid"
        }
    ]
}
```

### Order Book Feed (ws://localhost:8002/ws/orderbook/)
Provides real-time order book snapshots every second.

**Message Format**:
```json
{
    "bids": [
        {"price": 100.25, "quantity": 50},
        {"price": 100.20, "quantity": 30}
    ],
    "asks": [
        {"price": 100.30, "quantity": 40},
        {"price": 100.35, "quantity": 60}
    ]
}
```

---

## 🚀 Installation & Setup

### Prerequisites
- **Docker & Docker Compose** 
- **Python 3.8+** 
- **Redis** 

### Option 1: Docker Setup (Recommended)

1. **Clone the repository**:
```bash
git clone <repository-url>
cd order_api_microservices
```

2. **Build and start services**:
```bash
docker-compose up --build
```

This will start:
- Redis on port 6379
- Order Management Service on port 8000
- Trade Service on port 8001
- WebSocket Service on port 8002

### Option 2: Local Development Setup

1. **Create virtual environment**:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Start Redis**:
```bash
redis-server
```

4. **Run database migrations** (for each service):
```bash
cd services/order_management
python manage.py migrate
cd ../trade_service
python manage.py migrate
cd ../websocket_service
python manage.py migrate
```

5. **Start services** (in separate terminals):
```bash
# Terminal 1: Order Management Service
cd services/order_management
python manage.py runserver 8000

# Terminal 2: Trade Service
cd services/trade_service
python manage.py runserver 8001

# Terminal 3: WebSocket Service
cd services/websocket_service
uvicorn asgi:application --host 0.0.0.0 --port 8002 --reload
```

---


### Service Health Check

Once running, verify services are healthy:

```bash
# Order Management Service
curl http://localhost:8000/health/

# Trade Service
curl http://localhost:8001/health/

curl http://localhost:8002/health/

```

---

## 📝 API Usage Examples

### 1. Place a Buy Order

```bash
curl -X POST http://localhost:8000/orders/ \
  -H "Content-Type: application/json" \
  -d '{
    "side": "buy",
    "quantity": 100,
    "price": 150.25,
    "user_id": "123e4567-e89b-12d3-a456-426614174000"
  }'
```

### 2. Place a Sell Order

```bash
curl -X POST http://localhost:8000/orders/ \
  -H "Content-Type: application/json" \
  -d '{
    "side": "sell",
    "quantity": 50,
    "price": 150.20,
    "user_id": "123e4567-e89b-12d3-a456-426614174000"
  }'
```

### 3. Get Order Details

```bash
curl http://localhost:8000/orders/987fcdeb-51a2-43d7-8f9e-123456789abc/
```

### 4. Modify Order Price

```bash
curl -X PUT http://localhost:8000/orders/987fcdeb-51a2-43d7-8f9e-123456789abc/ \
  -H "Content-Type: application/json" \
  -d '{
    "price": 150.30
  }'
```

### 5. Cancel Order

```bash
curl -X DELETE http://localhost:8000/orders/987fcdeb-51a2-43d7-8f9e-123456789abc/
```

### 6. List Orders with Filters

```bash
# Get active buy orders
curl "http://localhost:8000/orders/?status=ACTIVE&side=buy"

# Get orders for specific user
curl "http://localhost:8000/orders/?user_id=123e4567-e89b-12d3-a456-426614174000"

# Paginated results
curl "http://localhost:8000/orders/?page=1&page_size=10"
```

### 7. Get Order Book Snapshot

```bash
# Get top 5 levels
curl http://localhost:8001/orderbook/

# Get top 10 levels
curl "http://localhost:8001/orderbook/?depth=10"
```


### 8. Get Trade History

```bash
# Get recent trades
curl http://localhost:8001/trades/

# Get paginated trades
curl "http://localhost:8001/trades/?page=1&page_size=20"
```

### 9. Settle a Trade -- ADD-ON Functionality

```bash
curl -X POST http://localhost:8001/trades/trade-uuid/settle/

```
### 10. Optimisation Techniques (Future Improvements)

- **User Authentication**  
  Implement authentication & authorization for secure order placement and trade access.  

- **Stock Identifiers**  
  Orders should be tied to specific stock/instrument IDs for clarity and scalability.  

- **Redis for Order Management**  
  Use Redis as a fast in-memory store to manage the order book and handle sequential DB sync updates.  

- **Asynchronous Operations**  
  Increase async usage for DB writes, Redis updates, and background tasks to reduce latency.  

- **Database Indexing**  
  Add indexes on frequently queried columns (e.g., `order_id`, `status`) to improve performance.  

- **Cron Jobs**  
  Automate business rules like marking pending orders as **FAILED** once the trading day completes.  

- **Queues (deque)**  
  Utilize deque structures to optimize workflows such as order matching, FIFO task execution, and retries.  

- **Consistent API Response Structure**  
  Standardize responses across all endpoints (200–300 success codes, 400 bad requests, 404 not found, etc.) for better client-side handling.  
