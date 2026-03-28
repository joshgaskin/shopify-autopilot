# AutoPilot — AI Agent Command Center for Shopify

## What We Built
5 autonomous AI agents that monitor, decide, and act on a Shopify store. Each agent has a distinct personality powered by Claude (Haiku) and takes real actions — product deactivation, purchase orders, discount codes, email drafts, customer segmentation.

### Agents
| Agent | Domain | What They Do |
|-------|--------|-------------|
| **Rick** | Operations | Deactivates zero-stock products, stockout alerts, health checks |
| **Hank** | Supply Chain | Scores products (Core/Strong/Slow/Exit), creates draft POs, reorder recs |
| **Ron** | Finance | Detects slow movers, creates discount codes in local DB |
| **Marty** | Marketing | RFM customer segmentation, drafts win-back + VIP email campaigns |
| **Marcus** | Chief of Staff | Coordinates all agents, deploys storefront widget, daily insights |

### How It Works
- **Backend** (`backend/app/agents/`): Orchestrator runs every 60s as an asyncio background task. Each cycle: load data → score products → detect issues → take actions → narrate via Claude → persist to SQLite.
- **Frontend** (`frontend/pages/autopilot.tsx`): Polls `/agents/states`, `/agents/actions`, `/agents/stats` every 5s. Pure read-only dashboard — agents run independently of the browser.
- **Shopify integration**: Agents attempt Shopify mutations (GraphQL/REST) first. When Shopify is unavailable, all actions are applied to the local SQLite database. The wiring exists for: product status updates, tag mutations, price rules, discount codes, ScriptTag injection.
- **Seed data**: When Shopify sync fails, `backend/app/agents/seed.py` creates 25 products, ~200 orders, 40 customers with realistic velocity patterns to trigger all agent behaviors.

### Key Files
- `backend/app/agents/orchestrator.py` — Main agent loop, all 5 agents
- `backend/app/agents/intelligence.py` — Scoring, stockout detection, RFM segmentation
- `backend/app/agents/personas.py` — Claude system prompts per agent
- `backend/app/agents/voice.py` — Claude API client for personality narration
- `backend/app/agents/models.py` — AgentAction, PurchaseOrder, Discount SQLAlchemy models
- `frontend/components/AgentDialogue.tsx` — Chat-style agent feed with avatars
- `frontend/pages/autopilot.tsx` — Command center with 4 tabs
- `frontend/pages/purchase-orders.tsx` — PO management page
- `frontend/pages/segments.tsx` — Customer segmentation with donut chart

---

# Shopify Hackathon — Builder's Guide (Starter Repo Docs)

## What You Have
A working Next.js 14 dashboard connected to a real Shopify store with live data flowing.
Your store has real products, customers, and orders — plus new orders arrive every 30-120 seconds via our order simulator.

## Quick Start
1. `cp .env.example .env` — paste your ACCESS_TOKEN and STORE_URL from your team card
2. `npm run setup` — installs frontend + backend dependencies
3. `npm run dev` — starts both frontend (localhost:3000) and backend (localhost:8000)
4. Open http://localhost:3000 — you should see a working dashboard with live data

## Your Store
- **Dashboard**: http://localhost:3000
- **Store Admin**: https://{STORE_URL}/admin (credentials on your team card)
- **Storefront**: https://{STORE_URL} (password: growzilla)
- Orders flow in live every 30-120 seconds — your data grows in real-time

## Architecture
```
Your laptop:
├── Next.js frontend        (localhost:3000)
├── FastAPI backend          (localhost:8000)
├── SQLite                   (hackathon.db)
└── .env                     (SHOPIFY_ACCESS_TOKEN + SHOPIFY_STORE_URL)
```

Everything runs locally. The backend handles Shopify GraphQL, REST, rate limits, data sync, and the order simulator.
All API calls go through `lib/api.ts` which talks to your local backend at localhost:8000.

## API Reference

Base URL: http://localhost:8000 (no auth needed — everything runs locally)

### Store Info
`api.getStore()` → StoreInfo
Returns: domain, name, currency, product_count, order_count, customer_count, last_sync_at

### Products
`api.getProducts({ page?, limit?, search?, status? })` → PaginatedResponse<Product>
`api.getProduct(id)` → Product

Product fields: id, title, handle, status, vendor, product_type, price_min, price_max, variants[], collections[], featured_image_url, inventory_total, created_at, updated_at
Variant fields: id, title, price, sku, inventory_quantity

### Orders
`api.getOrders({ page?, limit?, status?, since? })` → PaginatedResponse<Order>
`api.getOrder(id)` → Order

Order fields: id, order_number, total_price, subtotal_price, total_discounts, total_tax, currency, financial_status (paid|pending|refunded|partially_refunded), fulfillment_status (fulfilled|partial|unfulfilled|null), line_items[], customer_id, customer_email, customer_name, discount_codes[], landing_site, referring_site, processed_at, created_at, is_simulated

LineItem fields: title, variant_title, quantity, price

### Customers
`api.getCustomers({ page?, limit?, search? })` → PaginatedResponse<Customer>

Customer fields: id, email, first_name, last_name, orders_count, total_spent, tags[], created_at, last_order_at

### Inventory
`api.getInventory()` → InventoryLevel[]

InventoryLevel fields: variant_id, product_id, product_title, variant_title, sku, quantity, location

### Analytics
`api.getRevenue(period)` → { series: RevenueDataPoint[] }  — period: '7d' | '30d' | '90d'
`api.getTopProducts(limit)` → { products: TopProduct[] }
`api.getHourlyPatterns()` → { hours: { hour, avg_orders, avg_revenue }[] }
`api.getCustomerCohorts()` → { cohorts: { week, customers, retention_rates[] }[] }

RevenueDataPoint: { date, revenue, orders, aov }
TopProduct: { id, title, revenue, units_sold }

### Real-Time Events (SSE)
`useEventStream(maxEvents?)` → { events: LiveEvent[], lastEvent, connected }

Events arrive in real-time: new_order, product_update, inventory_change, refund_issued, customer_created
Each event has: id, event_type, payload (varies by type), created_at

### Actions (Write to Shopify)
`api.createDraftOrder(lineItems)` — Create a draft order
`api.createDiscount(code, percentage)` — Create a discount code
`api.sendEmail(to, subject, html)` — Send an email notification
`api.injectStorefrontScript(src)` — Add a JS widget to your store's storefront
`api.shopifyGraphQL(query, variables?)` — Raw Shopify GraphQL (advanced escape hatch)

## Available Components

### Layout
- `Shell` — Dashboard shell with sidebar nav + topbar. Wrap every page in this.
  `<Shell title="Page Title">{children}</Shell>`

### Data Display
- `KPICard` — Metric card: `<KPICard title="Revenue" value="$12,450" change={12.5} prefix="$" />`
- `DataTable` — Sortable paginated table: `<DataTable columns={cols} data={rows} />`
- `LiveFeed` — Real-time event ticker (uses SSE internally)
- `Badge` — Status pill: `<Badge variant="success">Paid</Badge>`
- `EmptyState` — Empty state placeholder

### Charts (pure SVG, no external libraries)
- `LineChart` — `<LineChart data={[{label, value}]} color="#00FF94" />`
- `BarChart` — `<BarChart data={[{label, value}]} horizontal />`
- `DonutChart` — `<DonutChart segments={[{label, value, color}]} centerLabel="Total" centerValue="$5K" />`
- `Sparkline` — Inline mini chart for KPI cards: `<Sparkline data={[1,3,2,5,4]} />`
- `HeatMap` — Grid heatmap for cohorts/time patterns: `<HeatMap data={grid} xLabels={[...]} yLabels={[...]} />`

### UI Primitives
- `Button` — `<Button variant="primary|secondary|ghost" size="sm|md">Text</Button>`
- `Card` — `<Card title="Section" subtitle="Optional">{content}</Card>`
- `Modal` — `<Modal open={bool} onClose={fn} title="Title">{content}</Modal>`
- `Select` — `<Select options={[{value, label}]} value={v} onChange={fn} />`
- `Tabs` — `<Tabs tabs={[{key, label}]} active={key} onChange={fn} />`
- `DateRange` — `<DateRange value="7d" onChange={fn} />` — presets: 7d, 30d, 90d, custom

## Available Hooks
- `useApi(fetcher, deps)` — Generic data fetching: `const { data, loading, error, refetch } = useApi(() => api.getProducts(), [])`
- `useProducts(params?)` — Products with pagination/search
- `useOrders(params?)` — Orders with filters
- `useCustomers(params?)` — Customer list
- `useRevenue(period)` — Revenue time series
- `useTopProducts(limit)` — Best sellers
- `useEventStream(maxEvents)` — Real-time SSE events
- `useInventory()` — Stock levels

## Adding New Features

### New Page
Create `frontend/pages/my-page.tsx`:
```tsx
import Shell from '../components/Shell'
import { useApi } from '../hooks/useApi'
import { api } from '../lib/api'

export default function MyPage() {
  const { data, loading } = useApi(() => api.getProducts(), [])

  return (
    <Shell title="My Page">
      {loading ? <div>Loading...</div> : (
        // Your UI here
      )}
    </Shell>
  )
}
```
It's automatically routed at `/my-page`. No router config needed.

### New Component
Create `frontend/components/MyComponent.tsx`, import and use it. Follow existing patterns in the components/ directory.

### New API Call
All API calls go through `lib/api.ts`. Add new methods there if needed.
For raw Shopify GraphQL: `api.shopifyGraphQL(query, variables)`

### Storefront Widget
Create a JS file in `public/`, then inject it:
```tsx
// After building your widget at public/my-widget.js
await api.injectStorefrontScript(`${window.location.origin}/my-widget.js`)
// Visit your store URL to see it live
```

## Design Rules (Linear/Apple Style)
- **Backgrounds**: surface-0 (#0A0A0B), surface-1 (#151518), surface-2 (#1A1A1A)
- **Borders**: border (rgba(255,255,255,0.08)) — NO shadows on cards
- **Text**: text-primary (95% white), text-secondary (72%), text-tertiary (48%)
- **Accent**: accent (#00FF94) — sparingly, max 10% of screen
- **Spacing**: 4px grid. Generous whitespace. p-4 cards, gap-6 sections
- **Radius**: rounded-md buttons, rounded-lg cards, rounded-xl modals
- **Motion**: 150ms transitions, ease-out only. No glow, pulse, or bounce.
- **Typography**: 13px body, 12px labels, 16px section headers
- **Rule of thumb**: "Would this look at home in Linear?" If no, simplify.

## Example Prompts (copy-paste to Claude Code)

### Inventory Predictor
"Create a page at /predictions that calculates days-until-stockout for each product. Use order data to compute 7-day sales velocity per product (sum quantities from recent orders grouped by product). Display a table with columns: Product, Current Stock, Daily Velocity, Days Until Stockout. Color-code: red < 3 days, yellow < 7, green > 7. Add a LineChart showing inventory projection for the selected product."

### Customer Segments
"Build a page at /segments that performs RFM analysis. Fetch all customers, calculate Recency (days since last order), Frequency (order count), Monetary (total spent). Score each 1-5. Create 4 segments: Champions (R>=4,F>=4,M>=4), Loyal (F>=3,M>=3), At Risk (R<=2,F>=3), Lost (R<=2,F<=2). Show a DonutChart of segment sizes and a DataTable listing customers with their segment, scores, and total spent."

### Live Anomaly Detector
"Create /anomalies page. Fetch hourly patterns from api.getHourlyPatterns() to get baseline averages. Use useEventStream() to count orders in the current hour. Compare current count vs baseline avg for this hour. Display: current hour stats, baseline stats, deviation percentage. Flag anomaly if >2 standard deviations. Show a HeatMap of expected vs actual by hour for today."

### Storefront Widget
"Build a low-stock warning widget. Create a file at public/low-stock-widget.js that: fetches inventory from our API, finds products with <5 units, injects a floating banner on the storefront showing 'Only X left!' for the current product page. Then call api.injectStorefrontScript() to install it on the store. Test by visiting the store URL."

### Revenue Forecaster
"Create /forecast page. Fetch 90 days of revenue data using api.getRevenue('90d'). Implement simple linear regression on the daily revenue series to project the next 30 days. Show: historical data as solid LineChart, projected data as dashed line. Display KPICards for: projected 30-day revenue, growth rate, confidence interval. Add a DataTable of daily projections."

### Email Alert System
"Add a /alerts page where I can set up inventory alerts. Show a DataTable of all products with inventory levels. Let me set a threshold per product (default 5). When useEventStream() receives an inventory_change event and the quantity drops below threshold, show a toast notification AND call api.sendEmail() to send an alert. Store thresholds in localStorage."

## Project Structure
```
├── package.json            ← Root: `npm run dev` starts everything
├── .env                    ← Your credentials (ACCESS_TOKEN + STORE_URL)
├── CLAUDE.md               ← This file
│
├── backend/                ← FastAPI (runs on localhost:8000)
│   ├── app/
│   │   ├── main.py         ← FastAPI entry, CORS, lifespan
│   │   ├── config.py       ← Reads .env (token, store URL)
│   │   ├── database.py     ← SQLite + SQLAlchemy async
│   │   ├── models.py       ← Product, Order, Customer, Event
│   │   ├── shopify.py      ← Shopify REST + GraphQL client
│   │   ├── sync.py         ← Data sync (products, orders, customers)
│   │   ├── simulator.py    ← Order simulator (creates test orders)
│   │   ├── events.py       ← SSE event manager (real-time)
│   │   └── routers/        ← API endpoints
│   ├── seed.py             ← Loads curated product catalog
│   └── requirements.txt
│
├── frontend/               ← Next.js 14 (runs on localhost:3000)
│   ├── pages/              ← Add new pages here (auto-routed)
│   │   ├── _app.tsx        ← Global layout
│   │   ├── index.tsx       ← Dashboard home
│   │   ├── products.tsx    ← Product catalog
│   │   └── orders.tsx      ← Order history
│   ├── components/         ← Reusable components
│   │   ├── Shell.tsx       ← Dashboard layout (use on every page)
│   │   ├── KPICard.tsx     ← Metric cards
│   │   ├── DataTable.tsx   ← Sortable table
│   │   ├── LiveFeed.tsx    ← Real-time order ticker
│   │   ├── EmptyState.tsx  ← Empty state placeholder
│   │   ├── charts/         ← SVG chart components
│   │   │   ├── LineChart.tsx
│   │   │   ├── BarChart.tsx
│   │   │   ├── DonutChart.tsx
│   │   │   ├── Sparkline.tsx
│   │   │   └── HeatMap.tsx
│   │   └── ui/             ← Buttons, badges, modals, etc.
│   │       ├── Badge.tsx
│   │       ├── Button.tsx
│   │       ├── Card.tsx
│   │       ├── Modal.tsx
│   │       ├── Select.tsx
│   │       ├── DateRange.tsx
│   │       └── Tabs.tsx
│   ├── hooks/              ← Data fetching hooks
│   │   ├── useApi.ts
│   │   ├── useProducts.ts
│   │   ├── useOrders.ts
│   │   ├── useCustomers.ts
│   │   ├── useAnalytics.ts
│   │   ├── useEventStream.ts
│   │   └── useInventory.ts
│   ├── lib/
│   │   ├── api.ts          ← API client (all endpoints)
│   │   ├── types.ts        ← TypeScript types
│   │   ├── utils.ts        ← Formatters and helpers
│   │   └── constants.ts    ← API URL config
│   └── styles/globals.css  ← Tailwind + dark theme
│
├── docs/                   ← API reference + build ideas
├── scripts/                ← Token capture, preflight checks
└── hackathon.db            ← SQLite database (auto-created)
```

## Do NOT
- Set up Shopify authentication (the backend reads the token from .env)
- Write raw GraphQL (use the REST API, or api.shopifyGraphQL for escape hatch)
- Install external chart libraries (use the SVG components)
- Modify the backend database schema (SQLite auto-creates tables on startup)
- Worry about rate limits (the backend handles rate limiting and retries)

## Troubleshooting
- **Backend not starting** → Check your .env has SHOPIFY_ACCESS_TOKEN and SHOPIFY_STORE_URL
- **No data showing** → The backend auto-syncs on first start. Check terminal for sync logs, wait 30 seconds
- **SSE not connecting** → Make sure backend is running on :8000. The green dot in LiveFeed shows connection status
- **Charts empty** → Make sure the API returns data. Check browser console for errors
- **"Using demo data" banner** → Backend isn't reachable. Check that `npm run dev` started both servers
- **Page not loading** → Make sure you wrapped it in `<Shell>`. Check for TypeScript errors in terminal
- **Styles look wrong** → Use Tailwind classes only. Check globals.css is imported in _app.tsx
- **SQLite errors** → Delete `hackathon.db` and restart — it will re-sync from Shopify
