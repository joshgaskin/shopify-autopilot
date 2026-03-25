# API Reference

Base URL: `https://hackathon-pipe.growzilla.xyz` (configured via `NEXT_PUBLIC_API_URL` in `.env`)

## Authentication

Every request requires the `X-Team-Key` header:

```
X-Team-Key: gzh_your_team_key_here
```

The API client in `lib/api.ts` handles this automatically. You never need to set headers manually when using the `api` object or hooks.

## Error Responses

All errors follow this format:

```json
{
  "error": "Error description",
  "code": "ERROR_CODE",
  "status": 401
}
```

| Status | Code | Meaning |
|--------|------|---------|
| 400 | `BAD_REQUEST` | Invalid parameters (missing required field, bad format) |
| 401 | `UNAUTHORIZED` | Missing or invalid X-Team-Key header |
| 403 | `FORBIDDEN` | Valid key but no access to this resource |
| 404 | `NOT_FOUND` | Resource doesn't exist |
| 429 | `RATE_LIMITED` | Too many requests — wait and retry (The Pipe handles Shopify rate limits, but your own request rate is capped at ~60/min) |
| 500 | `INTERNAL_ERROR` | Something broke on our end |
| 502 | `SHOPIFY_ERROR` | Shopify API returned an error (passthrough only) |

## Pagination

All list endpoints return paginated responses:

```json
{
  "data": [...],
  "total": 142,
  "page": 1,
  "limit": 50,
  "has_more": true
}
```

Query parameters:
- `page` (integer, default: 1) — Page number
- `limit` (integer, default: 50, max: 250) — Items per page

---

## Endpoints

### GET /store

Returns information about your team's Shopify store.

**Request:**
```
GET /store
X-Team-Key: gzh_xxx
```

**Response:**
```json
{
  "domain": "hackathon-07.myshopify.com",
  "name": "Hackathon Team 07",
  "currency": "USD",
  "product_count": 45,
  "order_count": 312,
  "customer_count": 89,
  "last_sync_at": "2026-03-28T10:15:30Z"
}
```

**Notes:**
- If `last_sync_at` is null, the initial data sync hasn't completed yet. Wait 30 seconds and retry.
- Counts update as the order simulator creates new data.

---

### GET /products

Returns a paginated list of products with variants, images, and collections.

**Query Parameters:**
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| page | integer | 1 | Page number |
| limit | integer | 50 | Items per page (max 250) |
| search | string | — | Search by title (case-insensitive partial match) |
| status | string | — | Filter by status: `active`, `draft`, `archived` |

**Request:**
```
GET /products?page=1&limit=20&search=shirt&status=active
```

**Response:**
```json
{
  "data": [
    {
      "id": "gid://shopify/Product/8234567890",
      "title": "Classic Cotton T-Shirt",
      "handle": "classic-cotton-t-shirt",
      "status": "active",
      "vendor": "Hackathon Brand",
      "product_type": "Shirts",
      "price_min": 24.99,
      "price_max": 29.99,
      "variants": [
        {
          "id": "gid://shopify/ProductVariant/44567890123",
          "title": "Small / Black",
          "price": 24.99,
          "sku": "TSHIRT-S-BLK",
          "inventory_quantity": 42
        },
        {
          "id": "gid://shopify/ProductVariant/44567890124",
          "title": "Medium / Black",
          "price": 24.99,
          "sku": "TSHIRT-M-BLK",
          "inventory_quantity": 18
        }
      ],
      "collections": ["Summer Collection", "Bestsellers"],
      "featured_image_url": "https://cdn.shopify.com/s/files/1/xxx/products/tshirt.jpg",
      "inventory_total": 60,
      "created_at": "2026-03-20T08:00:00Z",
      "updated_at": "2026-03-28T09:30:00Z"
    }
  ],
  "total": 45,
  "page": 1,
  "limit": 20,
  "has_more": true
}
```

---

### GET /products/:id

Returns a single product with full details.

**Request:**
```
GET /products/gid://shopify/Product/8234567890
```

**Response:** Same shape as a single item from `/products` data array.

---

### GET /orders

Returns a paginated list of orders with line items, customer info, and discount details.

**Query Parameters:**
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| page | integer | 1 | Page number |
| limit | integer | 50 | Items per page (max 250) |
| status | string | — | Filter: `paid`, `pending`, `refunded`, `partially_refunded`, `unfulfilled`, `fulfilled` |
| since | string (ISO date) | — | Orders created after this date (e.g., `2026-03-27`) |

**Request:**
```
GET /orders?page=1&limit=20&status=paid&since=2026-03-27
```

**Response:**
```json
{
  "data": [
    {
      "id": "gid://shopify/Order/6234567890",
      "order_number": "#1042",
      "total_price": 89.97,
      "subtotal_price": 84.97,
      "total_discounts": 5.00,
      "total_tax": 7.20,
      "currency": "USD",
      "financial_status": "paid",
      "fulfillment_status": "fulfilled",
      "line_items": [
        {
          "title": "Classic Cotton T-Shirt",
          "variant_title": "Medium / Black",
          "quantity": 2,
          "price": 24.99
        },
        {
          "title": "Denim Jacket",
          "variant_title": "Large",
          "quantity": 1,
          "price": 34.99
        }
      ],
      "customer_id": "gid://shopify/Customer/7234567890",
      "customer_email": "sarah.chen@example.com",
      "customer_name": "Sarah Chen",
      "discount_codes": ["SUMMER10"],
      "landing_site": "/collections/summer",
      "referring_site": "https://www.google.com",
      "processed_at": "2026-03-28T11:23:45Z",
      "created_at": "2026-03-28T11:23:45Z",
      "is_simulated": true
    }
  ],
  "total": 312,
  "page": 1,
  "limit": 20,
  "has_more": true
}
```

**Notes:**
- `is_simulated: true` means the order was created by our order simulator (most orders during the hackathon).
- `landing_site` and `referring_site` may be null — the simulator generates realistic values for some orders.
- `discount_codes` is an array of code strings (can be empty).
- `fulfillment_status` can be null (meaning unfulfilled).

---

### GET /orders/:id

Returns a single order with full details.

**Request:**
```
GET /orders/gid://shopify/Order/6234567890
```

**Response:** Same shape as a single item from `/orders` data array.

---

### GET /customers

Returns a paginated list of customers with order history summary.

**Query Parameters:**
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| page | integer | 1 | Page number |
| limit | integer | 50 | Items per page (max 250) |
| search | string | — | Search by name or email (case-insensitive) |

**Request:**
```
GET /customers?page=1&limit=20&search=chen
```

**Response:**
```json
{
  "data": [
    {
      "id": "gid://shopify/Customer/7234567890",
      "email": "sarah.chen@example.com",
      "first_name": "Sarah",
      "last_name": "Chen",
      "orders_count": 5,
      "total_spent": 342.50,
      "tags": ["returning", "vip"],
      "created_at": "2026-03-20T14:00:00Z",
      "last_order_at": "2026-03-28T11:23:45Z"
    }
  ],
  "total": 89,
  "page": 1,
  "limit": 20,
  "has_more": true
}
```

**Notes:**
- `last_order_at` can be null if the customer has never ordered.
- `tags` are Shopify customer tags (array of strings, can be empty).
- `total_spent` is cumulative across all orders.

---

### GET /inventory

Returns current stock levels for all product variants.

**Request:**
```
GET /inventory
```

**Response:**
```json
[
  {
    "variant_id": "gid://shopify/ProductVariant/44567890123",
    "product_id": "gid://shopify/Product/8234567890",
    "product_title": "Classic Cotton T-Shirt",
    "variant_title": "Small / Black",
    "sku": "TSHIRT-S-BLK",
    "quantity": 42,
    "location": "Hackathon Warehouse"
  },
  {
    "variant_id": "gid://shopify/ProductVariant/44567890124",
    "product_id": "gid://shopify/Product/8234567890",
    "product_title": "Classic Cotton T-Shirt",
    "variant_title": "Medium / Black",
    "sku": "TSHIRT-M-BLK",
    "quantity": 18,
    "location": "Hackathon Warehouse"
  }
]
```

**Notes:**
- Returns a flat array (not paginated) — one entry per variant per location.
- `quantity` decreases in real-time as the order simulator creates orders.
- Most stores have a single location ("Hackathon Warehouse").

---

### GET /analytics/revenue

Returns a time series of daily revenue, order count, and average order value.

**Query Parameters:**
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| period | string | `30d` | Time period: `7d`, `30d`, or `90d` |

**Request:**
```
GET /analytics/revenue?period=7d
```

**Response:**
```json
{
  "series": [
    {
      "date": "2026-03-22",
      "revenue": 1245.50,
      "orders": 28,
      "aov": 44.48
    },
    {
      "date": "2026-03-23",
      "revenue": 1389.75,
      "orders": 31,
      "aov": 44.83
    },
    {
      "date": "2026-03-24",
      "revenue": 987.25,
      "orders": 22,
      "aov": 44.88
    }
  ]
}
```

**Notes:**
- `aov` is average order value (revenue / orders).
- Series is ordered chronologically.
- Data grows throughout the hackathon as the simulator creates orders.

---

### GET /analytics/top-products

Returns best-selling products ranked by revenue.

**Query Parameters:**
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| limit | integer | 10 | Number of products to return (max 50) |

**Request:**
```
GET /analytics/top-products?limit=5
```

**Response:**
```json
{
  "products": [
    {
      "id": "gid://shopify/Product/8234567890",
      "title": "Classic Cotton T-Shirt",
      "revenue": 2499.80,
      "units_sold": 100
    },
    {
      "id": "gid://shopify/Product/8234567891",
      "title": "Denim Jacket",
      "revenue": 1749.50,
      "units_sold": 50
    }
  ]
}
```

---

### GET /analytics/hourly-patterns

Returns average order volume and revenue by hour of day (0-23), computed from historical data.

**Request:**
```
GET /analytics/hourly-patterns
```

**Response:**
```json
{
  "hours": [
    { "hour": 0, "avg_orders": 0.8, "avg_revenue": 35.20 },
    { "hour": 1, "avg_orders": 0.5, "avg_revenue": 22.10 },
    { "hour": 9, "avg_orders": 3.2, "avg_revenue": 142.80 },
    { "hour": 14, "avg_orders": 4.1, "avg_revenue": 183.50 },
    { "hour": 23, "avg_orders": 1.1, "avg_revenue": 48.90 }
  ]
}
```

**Notes:**
- Always returns 24 entries (hours 0-23).
- Averages are computed across all days with data.
- Useful as a baseline for anomaly detection (compare current hour vs average).

---

### GET /analytics/customer-cohorts

Returns weekly customer cohorts with retention rates.

**Request:**
```
GET /analytics/customer-cohorts
```

**Response:**
```json
{
  "cohorts": [
    {
      "week": "2026-03-04",
      "customers": 12,
      "retention_rates": [100, 58.3, 41.7, 33.3]
    },
    {
      "week": "2026-03-11",
      "customers": 15,
      "retention_rates": [100, 46.7, 33.3]
    },
    {
      "week": "2026-03-18",
      "customers": 18,
      "retention_rates": [100, 55.6]
    },
    {
      "week": "2026-03-25",
      "customers": 22,
      "retention_rates": [100]
    }
  ]
}
```

**Notes:**
- Each cohort is a group of customers who placed their first order in that week.
- `retention_rates` is an array of percentages: index 0 is always 100 (the cohort week), index 1 is % who ordered again in week 2, etc.
- Newer cohorts have fewer retention data points.

---

### GET /events/stream

Server-Sent Events (SSE) endpoint. Opens a persistent connection that pushes real-time store events.

**Request:**
```
GET /events/stream
X-Team-Key: gzh_xxx
Accept: text/event-stream
```

**Event format:**
```
event: new_order
data: {"id":"evt_abc123","event_type":"new_order","payload":{"order_id":"gid://shopify/Order/6234567890","order_number":"#1042","total_price":89.97,"currency":"USD","items_count":3,"customer":{"name":"Sarah Chen","email":"sarah.chen@example.com","returning":true}},"created_at":"2026-03-28T11:23:45Z"}

event: inventory_change
data: {"id":"evt_def456","event_type":"inventory_change","payload":{"product_id":"gid://shopify/Product/8234567890","product_title":"Classic Cotton T-Shirt","variant_title":"Small / Black","old_quantity":42,"new_quantity":40,"change":-2},"created_at":"2026-03-28T11:23:46Z"}

event: refund_issued
data: {"id":"evt_ghi789","event_type":"refund_issued","payload":{"order_id":"gid://shopify/Order/6234567880","order_number":"#1035","refund_amount":34.99,"reason":"customer_request"},"created_at":"2026-03-28T11:25:00Z"}

event: customer_created
data: {"id":"evt_jkl012","event_type":"customer_created","payload":{"customer_id":"gid://shopify/Customer/7234567895","name":"Alex Kim","email":"alex.kim@example.com"},"created_at":"2026-03-28T11:26:00Z"}

event: product_update
data: {"id":"evt_mno345","event_type":"product_update","payload":{"product_id":"gid://shopify/Product/8234567890","title":"Classic Cotton T-Shirt","change":"price_updated","old_value":"24.99","new_value":"27.99"},"created_at":"2026-03-28T11:27:00Z"}
```

**Event types:**
| Type | Frequency | Description |
|------|-----------|-------------|
| `new_order` | Every 30-120s | New order created (by simulator or manually) |
| `inventory_change` | With each order | Stock level changed for a variant |
| `refund_issued` | ~5% of orders, delayed | Order was refunded |
| `customer_created` | With new customers | First-time customer |
| `product_update` | Occasional | Product price, title, or status changed |

**Usage in code:**
Use the `useEventStream()` hook — it handles connection, reconnection, and event parsing:
```tsx
const { events, lastEvent, connected } = useEventStream(50)
// events: last 50 events (LiveEvent[])
// lastEvent: most recent event
// connected: boolean (SSE connection status)
```

---

### GET /events/history

Polling fallback for recent events (use SSE when possible).

**Query Parameters:**
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| limit | integer | 50 | Number of events (max 200) |
| since | string (ISO date) | — | Events after this timestamp |

**Request:**
```
GET /events/history?limit=20&since=2026-03-28T11:00:00Z
```

**Response:**
```json
{
  "events": [
    {
      "id": "evt_abc123",
      "event_type": "new_order",
      "payload": { ... },
      "created_at": "2026-03-28T11:23:45Z"
    }
  ],
  "total": 20
}
```

---

## Write Endpoints

### POST /orders/draft

Creates a draft order in your Shopify store.

**Request:**
```json
POST /orders/draft
{
  "line_items": [
    {
      "variant_id": "gid://shopify/ProductVariant/44567890123",
      "quantity": 2
    },
    {
      "variant_id": "gid://shopify/ProductVariant/44567890130",
      "quantity": 1
    }
  ],
  "note": "Created by hackathon app"
}
```

**Response:**
```json
{
  "id": "gid://shopify/DraftOrder/9234567890",
  "order_number": "#D1005",
  "total_price": 84.97,
  "status": "open",
  "line_items": [
    {
      "title": "Classic Cotton T-Shirt",
      "variant_title": "Small / Black",
      "quantity": 2,
      "price": 24.99
    },
    {
      "title": "Denim Jacket",
      "variant_title": "Large",
      "quantity": 1,
      "price": 34.99
    }
  ],
  "created_at": "2026-03-28T12:00:00Z"
}
```

---

### POST /discounts

Creates a discount code on your Shopify store.

**Request:**
```json
POST /discounts
{
  "code": "HACKATHON20",
  "percentage": 20,
  "usage_limit": 100
}
```

**Response:**
```json
{
  "id": "gid://shopify/DiscountCode/1234567890",
  "code": "HACKATHON20",
  "percentage": 20,
  "usage_limit": 100,
  "usage_count": 0,
  "status": "active",
  "created_at": "2026-03-28T12:00:00Z"
}
```

**Notes:**
- `percentage` is 1-100 (whole numbers).
- `usage_limit` is optional (omit for unlimited uses).
- The discount applies to the entire order.

---

### POST /notifications/email

Sends a transactional email via Resend.

**Request:**
```json
POST /notifications/email
{
  "to": "team@example.com",
  "subject": "Low Stock Alert: Classic Cotton T-Shirt",
  "html": "<h1>Stock Alert</h1><p>Classic Cotton T-Shirt (Small / Black) is down to 3 units.</p><p>Current velocity: 5 units/day. Estimated stockout: tomorrow.</p>"
}
```

**Response:**
```json
{
  "id": "email_abc123",
  "status": "sent",
  "to": "team@example.com",
  "subject": "Low Stock Alert: Classic Cotton T-Shirt"
}
```

**Notes:**
- `html` supports full HTML (inline styles work best for email).
- Rate limited to 10 emails per minute per team.
- Emails are sent from `hackathon@growzilla.xyz`.

---

### POST /storefront/inject

Injects a JavaScript file into your store's storefront via Shopify ScriptTags.

**Request:**
```json
POST /storefront/inject
{
  "src": "https://your-app.vercel.app/widget.js"
}
```

**Response:**
```json
{
  "id": "gid://shopify/ScriptTag/1234567890",
  "src": "https://your-app.vercel.app/widget.js",
  "display_scope": "all",
  "created_at": "2026-03-28T12:00:00Z"
}
```

**Notes:**
- The script loads on every page of your storefront.
- The `src` URL must be publicly accessible (HTTPS required).
- You can host widget files in your `public/` folder and use a tunnel (ngrok) or deploy to Vercel.
- To update, inject a new script (old ones persist unless removed).
- Visit `https://{STORE_URL}` (password: `growzilla`) to see your widget live.

---

### POST /storefront/theme-snippet

Writes a Liquid snippet directly into your store's active theme.

**Request:**
```json
POST /storefront/theme-snippet
{
  "key": "snippets/hackathon-widget.liquid",
  "value": "<div id=\"hackathon-widget\" style=\"position:fixed;bottom:20px;right:20px;z-index:9999;\">{{ 'Loading...' }}</div><script src=\"https://your-app.vercel.app/widget.js\"></script>"
}
```

**Response:**
```json
{
  "key": "snippets/hackathon-widget.liquid",
  "status": "created",
  "theme_id": "gid://shopify/Theme/1234567890"
}
```

**Notes:**
- Advanced feature. Most teams should use `/storefront/inject` instead.
- Supports Liquid template syntax (Shopify's templating language).
- The snippet is written to the store's active theme.

---

### POST /shopify/graphql

Raw Shopify Admin GraphQL passthrough. Use this as an escape hatch when REST endpoints don't cover your needs.

**Request:**
```json
POST /shopify/graphql
{
  "query": "{ products(first: 5) { edges { node { id title totalInventory } } } }",
  "variables": {}
}
```

**Response:**
```json
{
  "data": {
    "products": {
      "edges": [
        {
          "node": {
            "id": "gid://shopify/Product/8234567890",
            "title": "Classic Cotton T-Shirt",
            "totalInventory": 60
          }
        }
      ]
    }
  }
}
```

**Notes:**
- Full Shopify Admin API 2024-01 GraphQL schema is available.
- The Pipe handles authentication and rate limiting.
- Use this only when the REST endpoints above don't cover your use case.
- Shopify GraphQL docs: https://shopify.dev/docs/api/admin-graphql

---

## Using the API Client

All endpoints are pre-wired in `lib/api.ts`. You never need to make raw fetch calls.

```tsx
import { api } from '../lib/api'

// Read data
const store = await api.getStore()
const products = await api.getProducts({ page: 1, limit: 20, search: 'shirt' })
const orders = await api.getOrders({ status: 'paid', since: '2026-03-27' })
const customers = await api.getCustomers({ search: 'chen' })
const inventory = await api.getInventory()
const revenue = await api.getRevenue('30d')
const topProducts = await api.getTopProducts(10)
const hourly = await api.getHourlyPatterns()
const cohorts = await api.getCustomerCohorts()

// Write data
await api.createDraftOrder([{ variant_id: 'gid://...', quantity: 2 }])
await api.createDiscount('SAVE20', 20)
await api.sendEmail('team@example.com', 'Alert', '<h1>Hello</h1>')
await api.injectStorefrontScript('https://your-app.com/widget.js')
await api.shopifyGraphQL('{ shop { name } }')
```

With hooks (recommended for React components):

```tsx
import { useProducts } from '../hooks/useProducts'
import { useOrders } from '../hooks/useOrders'
import { useRevenue } from '../hooks/useAnalytics'
import { useEventStream } from '../hooks/useEventStream'

function MyComponent() {
  const { data: products, loading } = useProducts({ search: 'shirt' })
  const { data: orders } = useOrders({ status: 'paid' })
  const { data: revenue } = useRevenue('30d')
  const { events, lastEvent, connected } = useEventStream(50)

  // ... render with data
}
```
