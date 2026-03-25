# Hackathon Starter Repo — Implementation Plan
> Growzilla × Claude Code Hackathon | March 28, 2026 | Forest City Marina Hotel, Malaysia

---

## The Core Idea

Builders fork one repo, paste two env vars, run `npm install && npm run dev`, and see a **working Shopify dashboard with live data** in under 5 minutes. Then they tell Claude Code what to build in plain English.

Everything hard (Shopify auth, GraphQL, data sync, webhooks, rate limits) is handled by a **shared hosted backend we call "The Pipe."** Teams never touch it. They consume clean REST + real-time events.

---

## Architecture: Three Layers

```
┌─────────────────────────────────────────────────────────────┐
│  LAYER 1: SHOPIFY                                           │
│  25 dev stores — free, full API access, test data loaded    │
│  Order Simulator creates 1-3 orders/min per store           │
│  Webhooks fire on every change → The Pipe catches them      │
└──────────────────────────┬──────────────────────────────────┘
                           │ GraphQL + Webhooks (abstracted away)
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  LAYER 2: THE PIPE (shared FastAPI backend on Render)       │
│                                                             │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────────┐  │
│  │  REST API    │  │  Webhooks    │  │  Order Simulator  │  │
│  │  /products   │  │  Catches all │  │  Creates realistic│  │
│  │  /orders     │  │  store events│  │  orders every     │  │
│  │  /customers  │  │  Pushes via  │  │  30-120 seconds   │  │
│  │  /inventory  │  │  SSE stream  │  │  per store        │  │
│  │  /analytics  │  │              │  │                   │  │
│  │  /actions    │  │              │  │  Patterns:        │  │
│  │  /storefront │  │              │  │  - Repeat buyers  │  │
│  │  /graphql    │  │              │  │  - Co-purchases   │  │
│  │  (passthru)  │  │              │  │  - Refunds        │  │
│  └──────┬───────┘  └──────┬──────┘  │  - Discount usage │  │
│         │                 │         └───────────────────┘  │
│  ┌──────┴─────────────────┴──────────────────────────────┐  │
│  │  Multi-Store Client: team_key → domain → access_token  │  │
│  │  Shopify GraphQL abstracted behind clean REST          │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  PostgreSQL — partitioned by team_key                   │  │
│  │  stores | products | orders | customers | events        │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  SSE: GET /events/stream                                │  │
│  │  → new_order | product_update | inventory_change        │  │
│  │  → customer_created | refund_issued                     │  │
│  └────────────────────────────────────────────────────────┘  │
└──────────────────────────┬──────────────────────────────────┘
                           │ REST + SSE (API key auth)
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  LAYER 3: TEAM'S APP (forked Next.js repo, localhost:3000)  │
│                                                             │
│  .env: TEAM_API_KEY=gzh_xxx  STORE_URL=team-07.myshopify   │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  CLAUDE.md — "The Brain"                              │   │
│  │  Full API reference, data schemas, component library, │   │
│  │  architecture rules, example prompts that just work   │   │
│  │                                                       │   │
│  │  Builder types: "build a page that predicts inventory │   │
│  │  stockout and sends email alerts"                     │   │
│  │  → Claude reads CLAUDE.md → builds the entire feature │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                             │
│  Starter app: working dashboard with KPIs, charts,          │
│  product table, live order feed — proof everything works    │
│                                                             │
│  Components: Shell, KPICard, DataTable, Charts, LiveFeed    │
│  Hooks: useApi, useEventStream, useProducts, useOrders      │
│  API client: typed, pre-wired, handles all auth             │
└─────────────────────────────────────────────────────────────┘
```

---

## Why This Works

| Problem | How we solve it |
|---------|----------------|
| "I spent 2 hours on Shopify OAuth" | **Eliminated.** The Pipe handles all auth. Teams use an API key. |
| "GraphQL schema is confusing" | **Abstracted.** Clean REST endpoints. No GraphQL unless you want it. |
| "My webhook keeps 401ing" | **Not their problem.** The Pipe catches webhooks and pushes via SSE. |
| "I have no data to work with" | **Order Simulator.** Live orders flowing every 30-120s. Growing dataset. |
| "I need to set up a database" | **Done.** The Pipe has PostgreSQL with synced data. Teams consume via API. |
| "How do I deploy to see it on the store?" | **Script tags.** `POST /storefront/inject` — widget appears on store instantly. |
| "I don't know how to use Shopify Partner Dashboard" | **They don't need to.** Zero Partner Dashboard interaction required. |
| "I'm debugging CORS/auth/env vars" | **Pre-configured.** Fork, paste 2 vars, `npm run dev`. |

---

## The Pipe — API Reference

### Authentication
Every request: `X-Team-Key: {TEAM_API_KEY}` header.
The API client in the starter repo handles this automatically.

### READ Endpoints (data already synced and cached)

```
GET /store                          → Store info, name, plan, currency
GET /products?page=1&limit=50       → Products with variants, images, collections
GET /products/:id                   → Single product detail
GET /orders?page=1&status=any       → Orders with line items, customer, discounts
GET /orders/:id                     → Single order detail
GET /customers?page=1               → Customers with order history summary
GET /customers/:id                  → Single customer with full order history
GET /inventory                      → Stock levels per variant per location
GET /collections                    → Product collections
GET /analytics/revenue?period=30d   → Time-series revenue, orders, AOV
GET /analytics/top-products?limit=10 → Best sellers by revenue + units
GET /analytics/customer-cohorts     → Cohort retention data (weekly)
GET /analytics/hourly-patterns      → Order volume by hour of day
GET /events/stream                  → SSE: new_order, product_update, inventory_change
GET /events/history?limit=100       → Recent events (polling fallback)
```

### WRITE Endpoints (actions on the store)

```
POST /orders/draft                  → Create draft order
POST /products                      → Create/update product
POST /discounts                     → Create discount code
POST /fulfillments/:order_id        → Fulfill an order
POST /notifications/email           → Send email (Resend, pre-configured)
POST /storefront/inject             → Inject JS widget into storefront
POST /storefront/theme-snippet      → Add Liquid snippet to theme
```

### Passthrough (escape hatch for advanced teams)

```
POST /shopify/graphql               → Raw Shopify GraphQL query
POST /shopify/rest/*                → Raw Shopify REST API proxy
```

> 90% of teams use the clean REST endpoints.
> 10% of advanced teams use passthrough for custom queries.
> Nobody debugs auth, rate limits, or pagination.

---

## The Order Simulator — Making It Feel Alive

This is what separates a demo from an experience. A background service on The Pipe that creates **realistic orders on every test store** throughout the hackathon.

### Behavior
- **Frequency**: 1-3 orders per minute per store (Poisson distribution)
- **Time variance**: Higher frequency during "business hours" (simulated)
- **Products**: Randomly selected from store's actual catalog
- **Customers**: Mix of new and returning (repeat buyers ~30%)
- **Order patterns**:
  - Single-item orders (60%)
  - Multi-item orders (30%)
  - High-value orders (10%)
  - Discount code usage (~15%)
  - Abandoned checkouts (~20%, created but not completed)
  - Refunds/cancellations (~5%, delayed by 5-10 min)
- **Fulfillment**: Auto-fulfilled after 2-5 minute delay (~70%)

### Why This Matters
- Dashboards update **in real-time** (not stale snapshots)
- Data **grows** during the hackathon (start ~100 orders, end ~500+)
- ML teams have a **living dataset** with emerging patterns
- Anomaly detection actually works (you can see spikes/dips)
- Cohort analysis shows real trends
- Inventory counts decrease realistically

### Events Pushed via SSE
```json
{
  "event": "new_order",
  "data": {
    "order_id": "gid://shopify/Order/12345",
    "order_number": "#1042",
    "total": "89.99",
    "currency": "USD",
    "items": 3,
    "customer": { "name": "Sarah Chen", "returning": true },
    "timestamp": "2026-03-28T11:23:45Z"
  }
}
```

Teams subscribe with `useEventStream()` hook (pre-built in starter) and see orders appear live.

---

## Shopify Dev Stores — Strategy

### Why Dev Stores (Not Official Test Stores)
- **Free.** Unlimited. No time restrictions.
- **Full API access.** Same scopes as live stores. No limitations.
- **Generated test data.** Check one box → products, orders, customers, collections, discounts pre-loaded.
- **Custom apps installable.** Via Dev Dashboard (not deprecated legacy method).
- **No Partner Dashboard access needed for teams.** We create everything upfront.

### App Permissions (ALL scopes — don't limit builders)
```
read_products, write_products,
read_orders, write_orders,
read_customers, write_customers,
read_inventory, write_inventory,
read_fulfillments, write_fulfillments,
read_shipping, write_shipping,
read_analytics,
read_themes, write_themes,
read_script_tags, write_script_tags,
read_content, write_content,
read_price_rules, write_price_rules,
read_discounts, write_discounts,
read_marketing_events, write_marketing_events,
read_reports,
read_checkouts, write_checkouts
```

This means teams can build **anything**: inventory management, customer analytics, storefront widgets, order automation, discount engines, fulfillment tools — zero permission blocks.

### Store Access Per Team
Each team gets:
1. **API access** via The Pipe (API key auth, clean REST)
2. **Store admin** at `hackathon-XX.myshopify.com/admin` (staff login)
3. **Storefront** at `hackathon-XX.myshopify.com` (password: `growzilla`)

The admin access lets them see orders flowing in, products changing, and the effect of any write operations they make. The storefront lets them see widgets they inject.

---

## The Forked Repo — What Teams Get

```
HackathonStarterRepo/
├── CLAUDE.md                        ← THE BRAIN (most important file)
├── .env.example                     ← TEAM_API_KEY + STORE_URL (2 vars)
├── package.json                     ← Next.js 14 + Tailwind + Framer Motion
├── next.config.js
├── tailwind.config.js               ← Dark theme tokens (Linear/Apple style)
├── tsconfig.json
│
├── pages/
│   ├── _app.tsx                     ← Global layout + API provider
│   ├── index.tsx                    ← Dashboard home (KPIs + revenue chart + live feed)
│   ├── products.tsx                 ← Product catalog (sortable table, search)
│   └── orders.tsx                   ← Order history (filterable, live-updating)
│
├── components/
│   ├── Shell.tsx                    ← Dashboard shell (sidebar + topbar + store name)
│   ├── KPICard.tsx                  ← Metric card with value + trend arrow + sparkline
│   ├── DataTable.tsx                ← Sortable, filterable, paginated table
│   ├── LiveFeed.tsx                 ← Real-time event ticker (SSE-powered)
│   ├── EmptyState.tsx               ← Placeholder for pages with no data yet
│   ├── charts/
│   │   ├── BarChart.tsx             ← SVG bar chart (horizontal + vertical)
│   │   ├── LineChart.tsx            ← SVG line chart (multi-series, tooltips)
│   │   ├── DonutChart.tsx           ← SVG donut chart (with center label)
│   │   ├── Sparkline.tsx            ← Inline mini chart (for KPI cards)
│   │   └── HeatMap.tsx              ← SVG heatmap (for cohorts, time patterns)
│   └── ui/
│       ├── Badge.tsx                ← Status badges (fulfilled, pending, etc.)
│       ├── Button.tsx               ← Primary, secondary, ghost variants
│       ├── Card.tsx                 ← Elevated card container
│       ├── Modal.tsx                ← Dialog with backdrop
│       ├── Select.tsx               ← Dropdown select
│       ├── DateRange.tsx            ← Date range picker (7d, 30d, 90d, custom)
│       └── Tabs.tsx                 ← Tab navigation
│
├── hooks/
│   ├── useApi.ts                    ← Core fetch wrapper (adds X-Team-Key header)
│   ├── useProducts.ts               ← Products with search, pagination, caching
│   ├── useOrders.ts                 ← Orders with filters, pagination
│   ├── useCustomers.ts              ← Customer data
│   ├── useAnalytics.ts              ← Revenue, top products, cohorts
│   ├── useEventStream.ts            ← SSE connection for real-time events
│   └── useInventory.ts              ← Stock levels
│
├── lib/
│   ├── api.ts                       ← Typed API client (all endpoints)
│   ├── types.ts                     ← Product, Order, Customer, Event types
│   ├── utils.ts                     ← formatCurrency, formatDate, cn()
│   └── constants.ts                 ← API base URL, event types
│
├── styles/
│   └── globals.css                  ← Tailwind base + dark theme utilities
│
└── public/
    └── favicon.ico
```

### What's Working on First `npm run dev`

The starter app is **not a blank canvas.** It's a working dashboard:

1. **Home page** — 4 KPI cards (Revenue, Orders, AOV, Customers) + revenue line chart + live order feed
2. **Products page** — Full product table with search, sort by price/title/inventory
3. **Orders page** — Order list with status filters, live-updating as simulator creates orders

This proves the setup works and gives teams a foundation to build on.

---

## CLAUDE.md — The Brain

This is the most important file in the repo. It's not documentation for humans — it's a **programming manual for Claude Code.** When a builder types "make an app that predicts inventory stockout", Claude reads this file and builds the entire feature.

### Structure

```markdown
# Shopify App Hackathon — Builder Guide

## What You Have
- A working Next.js dashboard connected to a real Shopify store
- Live data flowing (orders every 30-120 seconds)
- Full read/write access to products, orders, customers, inventory, storefront
- Pre-built components: charts, tables, cards, live feed
- 4 hours. Build something unreasonable.

## Your Store
- URL: ${STORE_URL} (set in .env)
- Admin: ${STORE_URL}/admin (credentials on your team card)
- Storefront: ${STORE_URL} (password: growzilla)
- Orders are flowing in live via our simulator — your data grows in real-time.

## API Reference
Base: https://hackathon-pipe.growzilla.xyz
Auth: X-Team-Key header (pre-configured in lib/api.ts)

### Products
GET /products → { data: Product[], total: number, page: number }
GET /products/:id → Product

Product = {
  id: string              // Shopify GID
  title: string
  handle: string          // URL slug
  status: "active" | "draft" | "archived"
  vendor: string
  product_type: string
  price_min: number
  price_max: number
  variants: Variant[]     // sizes, colors, etc.
  collections: string[]   // collection titles
  featured_image_url: string | null
  inventory_quantity: number  // total across locations
  created_at: string
  updated_at: string
}

### Orders
GET /orders → { data: Order[], total, page }
GET /orders/:id → Order

Order = {
  id: string
  order_number: string    // "#1042"
  total_price: number
  subtotal_price: number
  total_discounts: number
  total_tax: number
  currency: string
  financial_status: "paid" | "pending" | "refunded" | "partially_refunded"
  fulfillment_status: "fulfilled" | "partial" | "unfulfilled" | null
  line_items: LineItem[]
  customer: { id, email, name } | null
  discount_codes: string[]
  landing_site: string | null    // URL customer arrived from
  referring_site: string | null  // external referrer
  processed_at: string
  created_at: string
}

### Customers
GET /customers → { data: Customer[], total, page }
GET /customers/:id → Customer (includes full order history)

Customer = {
  id: string
  email: string
  first_name: string
  last_name: string
  orders_count: number
  total_spent: number
  created_at: string
  last_order_at: string | null
  tags: string[]
}

### Inventory
GET /inventory → InventoryLevel[]

InventoryLevel = {
  variant_id: string
  product_id: string
  product_title: string
  variant_title: string
  sku: string
  quantity: number
  location: string
}

### Analytics
GET /analytics/revenue?period=7d|30d|90d → { series: { date, revenue, orders, aov }[] }
GET /analytics/top-products?limit=10 → { products: { id, title, revenue, units_sold }[] }
GET /analytics/customer-cohorts → { cohorts: { week, customers, retention_rates: number[] }[] }
GET /analytics/hourly-patterns → { hours: { hour: 0-23, avg_orders, avg_revenue }[] }

### Real-Time Events (SSE)
GET /events/stream → Server-Sent Events

Hook: useEventStream() — already built in hooks/useEventStream.ts
Events: new_order, order_updated, product_update, inventory_change, refund_issued

Usage:
  const { events, lastEvent } = useEventStream()
  // events = last 50 events
  // lastEvent = most recent, updates in real-time

### Write Operations
POST /orders/draft → Create draft order
POST /products → Create product
POST /discounts → Create discount code
POST /fulfillments/:order_id → Fulfill order
POST /notifications/email → Send email { to, subject, html }
POST /storefront/inject → Add JS widget to storefront { script_url }

### Shopify Direct (advanced, escape hatch)
POST /shopify/graphql → { query: "...", variables: {} }
  Full Shopify Admin GraphQL API. Use only if REST endpoints don't cover your need.

## Architecture Rules
- New pages → pages/[name].tsx (auto-routed)
- New components → components/[Name].tsx
- Business logic → lib/[name].ts
- API calls → always use lib/api.ts client (handles auth + types)
- Styling → Tailwind classes only, dark theme (see tailwind.config.js)
- Charts → use or extend components/charts/ (SVG-based, no external libs)

## Available Components
[Full list with props and usage examples for each component]

## Design Rules (Linear/Apple Style)
- Background: #0A0A0B (base), #151518 (card), #1A1A1A (hover)
- Borders: rgba(255,255,255,0.08) — no shadows
- Text: 95% white (primary), 72% (secondary), 48% (tertiary)
- Accent: #00FF94 — use sparingly (max 10% of screen)
- Typography: 13px body, 12px labels, 16px headers
- Motion: 150ms transitions, ease-out only
- Self-check: "Would this look at home in Linear?"

## Example Prompts (copy-paste these to get started fast)

"Create a new page called /predictions that shows a table of all products with
a predicted days-until-stockout column. Calculate velocity from recent orders
(use /analytics and /orders endpoints). Color-code: red < 3 days, yellow < 7,
green > 7. Add a line chart showing inventory trend per product."

"Build a customer segmentation page at /segments. Use RFM analysis (recency,
frequency, monetary) on customer data. Show 4 segments in a 2x2 grid: Champions,
Loyal, At Risk, Lost. Each segment card shows count + avg spend + list of customers.
Use the DonutChart to show segment distribution."

"Add a live order feed widget to the home page that shows orders as they come in
using useEventStream(). Each order shows: customer name, items, total, time ago.
Animate new orders sliding in from the top. Play a subtle sound on high-value
orders (> $100)."

"Create an anomaly detection page at /anomalies. Fetch hourly order patterns
from /analytics/hourly-patterns and compare against current hour's actual orders
from /events/history. Flag if current volume is >2 standard deviations from
average. Show a heatmap of normal patterns vs actual."

## DO NOT
- Set up Shopify authentication (it's handled by The Pipe)
- Write GraphQL queries (use REST endpoints, or /shopify/graphql passthrough)
- Configure CORS or environment variables (pre-configured)
- Install chart libraries (use the SVG components in components/charts/)
- Debug webhook signatures (The Pipe handles all webhooks)
- Create a database (data lives in The Pipe's PostgreSQL)
```

---

## Builder Experience — Minute by Minute

```
TIME    WHAT HAPPENS
─────   ──────────────────────────────────────────────────────────
0:00    Kickoff. Get credential card. Open laptop.

0:02    Fork repo on GitHub.
        git clone https://github.com/[their-fork]/HackathonStarterRepo
        cd HackathonStarterRepo

0:03    cp .env.example .env
        # Paste TEAM_API_KEY and STORE_URL from card

0:05    npm install && npm run dev
        Open localhost:3000
        → See working dashboard: KPIs, revenue chart, live order feed
        → Orders appearing in real-time (simulator is running)
        → "Holy shit, this already works"

0:08    Open Claude Code in the repo.
        Claude reads CLAUDE.md automatically.
        Builder types: "Build a page that shows inventory predictions
        for each product based on sales velocity"
        → Claude builds it. Full page. Charts. Color-coded alerts.

0:15    The page works. Real data. Live updating.
        Builder starts customizing: "Make the cards more compact,
        add a sparkline showing last 7 days of sales per product"

0:25    Core feature is 80% done.
        Builder explores: visits their store admin at
        hackathon-XX.myshopify.com/admin → sees orders flowing in.
        "Can I add a widget to the storefront that shows a countdown
        for low-stock products?"
        → Claude uses POST /storefront/inject

0:40    App is functional. Now it's polish time.
        "Add transitions when new data arrives"
        "Make the table exportable to CSV"
        "Add email alerts for stockouts"

1:00+   Builder is in flow state. Iterating on their vision.
        Not debugging. Not fighting APIs. Just building.

4:00    Demo time. Builder shows a polished Shopify app that would
        take a solo developer 2-3 weeks to build normally.
```

---

## Pre-Event Setup (Albert does this)

### Phase 1: Shopify Infrastructure (~1.5 hours)

| # | Task | How | Time |
|---|------|-----|------|
| 1 | Create Shopify Partner account | partners.shopify.com (free) | 2 min |
| 2 | Create 25 dev stores | Dev Dashboard → Add dev store. Check "Generate test data". Name: `hackathon-01` through `hackathon-25` | 30 min |
| 3 | Create 25 apps in Dev Dashboard | One app per store. Request ALL scopes (see list above). | 30 min |
| 4 | Install each app on its store | App Home → Install → select store | 20 min |
| 5 | Create staff accounts | Each store gets a staff login (team07@hackathon.dev / hack2026team07) | 15 min |
| 6 | Set storefront password | All stores: "growzilla" | 5 min |

### Phase 2: The Pipe Deployment (~1 hour)

| # | Task | How | Time |
|---|------|-----|------|
| 7 | Build The Pipe backend | Extract Shopify client + data sync from ecomdash-api. Add: multi-store routing, API key auth, order simulator, SSE events. | The build task (next section) |
| 8 | Deploy to Render | New web service. PostgreSQL database. Environment variables. | 10 min |
| 9 | Register all 25 stores | Script: insert store records with domain + encrypted access token + team API key | 5 min |
| 10 | Run initial data sync | Script: sync all 25 stores (products, orders, customers from Shopify) | 10 min |
| 11 | Start order simulator | Enable the background task. Verify orders appearing. | 5 min |

### Phase 3: Starter Repo (~2 hours)

| # | Task | How | Time |
|---|------|-----|------|
| 12 | Build Next.js starter | Dashboard shell, KPI cards, charts, data table, live feed | The build task |
| 13 | Write CLAUDE.md | Full API reference, schemas, components, design rules, example prompts | 30 min |
| 14 | Write .env.example | TEAM_API_KEY and STORE_URL with descriptions | 2 min |
| 15 | Test end-to-end | Fresh clone → env setup → npm run dev → working dashboard | 15 min |
| 16 | Push to GitHub | Growzilla/HackathonStarterRepo | 2 min |

### Phase 4: Credential Cards (~30 min)

| # | Task | How | Time |
|---|------|-----|------|
| 17 | Generate credential cards | Script: for each team, output: API key, store URL, admin login, storefront password, quick start steps | 10 min |
| 18 | Print cards | Physical cards or QR codes linking to a private Gist per team | 20 min |

### Phase 5: Day-Before Verification

| # | Task | How | Time |
|---|------|-----|------|
| 19 | Verify all 25 stores have data | Hit /store for each team key, check product/order counts | 5 min |
| 20 | Verify order simulator is running | Check SSE stream for recent events | 2 min |
| 21 | Verify a fresh fork works | New GitHub account, fork, clone, env, npm run dev | 10 min |
| 22 | Verify CLAUDE.md works | Open Claude Code, paste an example prompt, confirm it builds correctly | 10 min |

---

## The Pipe — Build Spec

### What to Extract from ecomdash-api
- `services/shopify_client.py` — GraphQL client with rate limiting, retries, token decryption
- `services/data_sync.py` — Product + order sync logic (pagination, upserts)
- `models/` — Shop, Product, Order (simplified, remove UTM/insights/meta)
- `core/config.py` — Environment variable loading
- `core/database.py` — Async SQLAlchemy setup

### What to Build New
- **Multi-store routing** — API key → store lookup → use that store's credentials
- **API key auth middleware** — Simple header check, no JWT complexity
- **Order simulator service** — Background task, creates realistic orders via Shopify Admin API
- **SSE event stream** — FastAPI StreamingResponse, push webhook events + simulator events
- **Storefront endpoints** — ScriptTag creation, theme snippet injection via Admin API
- **GraphQL passthrough** — Forward raw queries to the correct store's API
- **Customer sync** — Add to data_sync (ecomdash doesn't sync customers currently)
- **Inventory endpoint** — Fetch current stock levels via GraphQL
- **Analytics endpoints** — Aggregate orders into time-series, top products, cohorts

### Models (Simplified)

```python
class Store(Base):
    id: UUID
    team_key: str           # gzh_xxx — unique per team
    domain: str             # hackathon-07.myshopify.com
    access_token_enc: str   # Fernet-encrypted Shopify token
    name: str
    currency: str
    sync_status: str        # pending | syncing | completed | error
    last_sync_at: datetime
    simulator_enabled: bool # default True

class Product(Base):
    id: str                 # Shopify GID
    store_id: UUID
    title: str
    handle: str
    status: str
    vendor: str
    product_type: str
    price_min: Decimal
    price_max: Decimal
    variants: JSONB         # [{id, title, price, sku, inventory_quantity}]
    collections: JSONB      # ["Summer Collection", "Bestsellers"]
    featured_image_url: str
    inventory_total: int
    created_at: datetime
    updated_at: datetime

class Order(Base):
    id: str                 # Shopify GID
    store_id: UUID
    order_number: str
    total_price: Decimal
    subtotal_price: Decimal
    total_discounts: Decimal
    total_tax: Decimal
    currency: str
    financial_status: str
    fulfillment_status: str
    line_items: JSONB
    customer_id: str
    customer_email: str
    customer_name: str
    discount_codes: JSONB
    landing_site: str
    referring_site: str
    processed_at: datetime
    created_at: datetime
    is_simulated: bool      # True = created by order simulator

class Customer(Base):
    id: str                 # Shopify GID
    store_id: UUID
    email: str
    first_name: str
    last_name: str
    orders_count: int
    total_spent: Decimal
    tags: JSONB
    created_at: datetime
    last_order_at: datetime

class Event(Base):
    id: UUID
    store_id: UUID
    event_type: str         # new_order, product_update, inventory_change, etc.
    payload: JSONB
    created_at: datetime
```

---

## Storefront Access — How Teams Modify the Store

Teams don't need Shopify Partner Dashboard. Three options, all through The Pipe:

### Option 1: Script Tag Injection (easiest)
```
POST /storefront/inject
{ "src": "https://your-vercel-app.com/widget.js" }
```
- The Pipe creates a ScriptTag on their Shopify store
- The JS file loads on every page of the storefront
- Team hosts the JS anywhere (Vercel, GitHub Pages, or even localhost via ngrok)
- Visit `hackathon-XX.myshopify.com` → see the widget

### Option 2: App Proxy (dynamic content)
- Pre-configured per store: `hackathon-XX.myshopify.com/apps/hackathon/*` → team's server
- Team creates a Next.js API route that returns HTML
- Shopify injects it into the store's theme
- Good for: product recommendations, custom pages, dynamic content

### Option 3: Theme API (advanced)
```
POST /storefront/theme-snippet
{ "key": "snippets/hackathon-widget.liquid", "value": "<div>...</div>" }
```
- The Pipe writes directly to the store's active theme
- Team can add Liquid snippets that render in the storefront
- Good for: checkout customization, product page additions

### How It Looks

Builder says to Claude Code:
> "Add a floating widget to my store's storefront that shows a countdown
> timer for products with less than 5 units in stock"

Claude:
1. Creates `/public/storefront-widget.js` with the widget logic
2. The widget fetches from The Pipe's `/inventory` endpoint
3. Calls `POST /storefront/inject` with the script URL
4. Builder visits `hackathon-XX.myshopify.com` → sees the widget

---

## Ideas Document (included in repo as docs/IDEAS.md)

### Difficulty: Easy (great for first hackathon)
1. **Smart Dashboard** — Revenue forecasting, customer lifetime value predictions, product performance scoring
2. **Inventory Sentinel** — Predict stockouts based on sales velocity, email alerts, reorder suggestions
3. **Customer DNA** — RFM segmentation, churn prediction, personalized discount recommendations

### Difficulty: Medium
4. **Store Detective** — Anomaly detection on orders (unusual volumes, suspicious patterns, fraud signals)
5. **Price Oracle** — Dynamic pricing suggestions based on demand patterns, competitor-style analysis, margin optimization
6. **Fulfillment Brain** — Smart fulfillment prioritization, shipping cost optimization, delivery time predictions

### Difficulty: Hard (for cracked ML/AI engineers)
7. **Demand Prophet** — Time-series forecasting with seasonality, promotion impact modeling, inventory optimization
8. **Customer Journey AI** — Map customer paths from landing_site/referring_site data, predict conversion likelihood, suggest interventions
9. **AI Store Clerk** — Storefront widget that recommends products based on browsing patterns and purchase co-occurrence matrices
10. **Revenue Autopilot** — End-to-end: predict demand → auto-create discounts for slow movers → auto-reorder fast movers → email customers about back-in-stock

---

## Build Order (Implementation Sequence)

### Week of March 24-27

```
Day 1 (Mon): The Pipe — Core
├── Extract Shopify client from ecomdash-api
├── Multi-store routing + API key auth
├── Store, Product, Order, Customer models
├── Data sync service (products + orders + customers)
├── REST read endpoints (/products, /orders, /customers, /store)
└── Deploy to Render + create PostgreSQL

Day 2 (Tue): The Pipe — Features
├── Order simulator service
├── SSE event streaming
├── Analytics endpoints (revenue, top-products, cohorts, patterns)
├── Write endpoints (draft orders, products, discounts, email)
├── Storefront endpoints (script tags, theme snippets)
├── GraphQL passthrough
└── Inventory endpoint

Day 3 (Wed): Starter Repo
├── Next.js 14 project setup (Tailwind, dark theme)
├── Dashboard shell (sidebar, topbar)
├── Components (KPICard, DataTable, charts, LiveFeed, ui/)
├── Hooks (useApi, useProducts, useOrders, useEventStream, etc.)
├── API client (typed, all endpoints)
├── Three starter pages (home, products, orders)
└── Verify: npm run dev shows working dashboard

Day 4 (Thu): Polish + CLAUDE.md
├── Write CLAUDE.md (API reference, schemas, components, prompts)
├── Write IDEAS.md
├── Create 25 dev stores + apps + staff accounts
├── Register all stores in The Pipe
├── Run initial sync + start simulator
├── End-to-end test: fresh fork → working dashboard
├── Generate + print credential cards
└── Final verification: Claude Code builds a feature from example prompt
```

---

## Open Questions

1. **Backend hosting cost** — The Pipe on Render (starter plan ~$7/mo) + PostgreSQL (~$7/mo). Or use existing ecomdash-api Render instance with new routes?
2. **Order simulator write API costs** — Shopify rate limits: 40 requests/second for private apps. With 25 stores × 1-3 orders/min, we need ~1 request/second. Well within limits.
3. **Email integration** — Use existing Resend setup from Growzilla? Or a simpler transactional email provider?
4. **Post-hackathon** — Do teams keep access to their stores? How long do we run the simulator? Consider a "freeze" date.
5. **WiFi reliability** — If hotel WiFi is spotty, should we pre-bundle data snapshots as JSON fallback? (Probably yes, as insurance.)
6. **Vercel for storefront widgets** — Each team would need their own Vercel deployment for public URLs. Alternative: we host a simple file server on The Pipe for uploaded widget scripts.

---

## Summary

| Layer | What | Who Maintains |
|-------|------|---------------|
| Shopify Dev Stores | 25 stores with test data + live orders | Albert (pre-event) |
| The Pipe | Shared backend, REST API, order simulator, SSE | Albert (deployed on Render) |
| Starter Repo | Next.js dashboard + CLAUDE.md | Albert (on GitHub) |
| Team's App | Forked repo, customized by each team | Builders (during hackathon) |

**The CLAUDE.md is the product.** The starter code is scaffolding. The CLAUDE.md turns "predict inventory stockout" into a working feature because Claude Code has perfect context on every endpoint, every data shape, every component, and every design rule.

Builders don't read docs. Claude reads the CLAUDE.md and builds for them.
