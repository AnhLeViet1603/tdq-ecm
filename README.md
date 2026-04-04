# 🛒 E-Commerce Microservices Platform

Django-based microservices e-commerce platform với 10 services độc lập, PostgreSQL, và Docker.

## Architecture

```
Client → Gateway (8000)
           ├── /api/auth/       → Auth Service      (8001) - JWT, RBAC
           ├── /api/products/   → Product Service   (8002) - Catalog, Categories
           ├── /api/inventory/  → Inventory Service (8003) - Stock, Warehouses
           ├── /api/cart/       → Cart Service      (8004) - Shopping Cart
           ├── /api/orders/     → Order Service     (8005) - Orders
           ├── /api/payments/   → Payment Service   (8006) - Transactions
           ├── /api/promotions/ → Promotion Service (8007) - Coupons
           ├── /api/reviews/    → Review Service    (8008) - Reviews & Ratings
           └── /api/shipping/   → Shipping Service  (8009) - Tracking
```

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Framework | Django 5.0 + Django REST Framework |
| Auth | djangorestframework-simplejwt |
| Database | PostgreSQL 16 (1 instance, 9 databases) |
| Gateway | Django + httpx reverse proxy |
| Container | Docker + Docker Compose |
| Python | 3.12 |

## Quick Start

```bash
# 1. Clone & configure
cp .env.example .env
# Edit .env with your secrets

# 2. Start all services
docker compose up --build -d

# 3. Run migrations
make migrate-all

# 4. Create admin user
make createsuperuser-auth

# 5. Check health
curl http://localhost:8000/health/
curl http://localhost:8001/health/
```

## Service Ports

| Service | Port | Description |
|---------|------|-------------|
| gateway | 8000 | API Gateway / Reverse Proxy |
| auth | 8001 | Authentication & Identity (JWT + RBAC) |
| product | 8002 | Product Catalog |
| inventory | 8003 | Inventory & Stock Management |
| cart | 8004 | Shopping Cart |
| order | 8005 | Order Management |
| payment | 8006 | Payment Processing |
| promotion | 8007 | Coupons & Discounts |
| review | 8008 | Reviews & Ratings |
| shipping | 8009 | Shipping & Tracking |
| postgres | 5432 | PostgreSQL (9 databases) |

## API Endpoints

### Authentication (via gateway: /api/auth/...)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/auth/register/ | Register new user |
| POST | /api/auth/login/ | Login → returns JWT tokens |
| POST | /api/auth/token/refresh/ | Refresh access token |
| POST | /api/auth/logout/ | Blacklist refresh token |
| GET | /api/auth/me/ | Current user profile |
| PUT | /api/auth/me/ | Update profile |
| POST | /api/auth/change-password/ | Change password |

### Products (/api/products/...)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/products/ | List products (public, paginated) |
| GET | /api/products/{id}/ | Product detail |
| POST | /api/products/ | Create product (admin) |
| GET | /api/products/categories/ | List categories |

### Cart (/api/cart/...)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/cart/me/ | View my cart |
| POST | /api/cart/add/ | Add item to cart |
| DELETE | /api/cart/remove/{item_id}/ | Remove item |
| DELETE | /api/cart/clear/ | Clear cart |

### Orders (/api/orders/...)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/orders/ | My orders |
| POST | /api/orders/ | Create order |
| GET | /api/orders/{id}/ | Order detail |
| POST | /api/orders/{id}/update-status/ | Change order status |

### Promotions (/api/promotions/...)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/promotions/coupons/ | List coupons (admin) |
| POST | /api/promotions/coupons/validate/ | Validate coupon code |

## Inter-Service JWT Authentication

Services communicate securely using shared JWT tokens:

1. **Auth Service** issues JWT tokens with embedded user info (email, roles)
2. **Downstream services** verify tokens locally using shared `JWT_SECRET_KEY`
3. No extra API call needed — user info extracted from token payload

```python
# Token payload contains:
{
    "user_id": "uuid",
    "email": "user@example.com",
    "full_name": "John Doe",
    "roles": ["customer"],
    "is_staff": false
}
```

## Project Structure

```
Ecommerce/
├── docker-compose.yml          # All 10 services + PostgreSQL
├── init-db.sql                 # Creates 9 databases on first boot
├── .env / .env.example
├── Makefile                    # Helper commands
│
├── shared/                     # Shared Python utilities
│   ├── base_model.py           # UUID pk + auto timestamps
│   ├── auth_middleware.py      # JWT verification for downstream services
│   ├── pagination.py           # StandardPagination
│   └── responses.py            # success/error response helpers
│
└── services/
    ├── gateway/    (8000)      # Reverse proxy with httpx
    ├── auth/       (8001)      # JWT + RBAC (simplejwt)
    ├── product/    (8002)      # Category, Product, Attribute
    ├── inventory/  (8003)      # Warehouse, Stock, StockHistory
    ├── cart/       (8004)      # Cart, CartItem
    ├── order/      (8005)      # Order, OrderItem, OrderHistory
    ├── payment/    (8006)      # Transaction, PaymentMethod
    ├── promotion/  (8007)      # Coupon, Discount, UsageLimit
    ├── review/     (8008)      # Review, ReviewMedia
    └── shipping/   (8009)      # Carrier, Shipment, TrackingLog
```

## Make Commands

```bash
make up                  # Start all services
make down                # Stop all services
make build               # Rebuild images
make logs                # Tail all logs
make logs-auth           # Tail auth service logs
make migrate-all         # Run migrations for all services
make migrate-auth        # Migrate specific service
make shell-auth          # Open Django shell in auth service
make restart-gateway     # Restart specific service
make clean               # Stop and remove volumes
```

## Environment Variables

See `.env.example` for all required variables. Key ones:

```env
DJANGO_SECRET_KEY=...    # Django secret key
JWT_SECRET_KEY=...       # SAME key shared across all services
POSTGRES_PASSWORD=...    # PostgreSQL password
```

> ⚠️ **Important:** `JWT_SECRET_KEY` must be identical across all services for token verification to work.

## Database Access

Each service connects to its own PostgreSQL database:

| Service | Database |
|---------|----------|
| auth | db_auth |
| product | db_product |
| inventory | db_inventory |
| cart | db_cart |
| order | db_order |
| payment | db_payment |
| promotion | db_promotion |
| review | db_review |
| shipping | db_shipping |

Connect directly: `psql -h localhost -p 5432 -U postgres -d db_auth`
