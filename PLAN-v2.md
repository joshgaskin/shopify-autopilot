# Hackathon Starter Repo — Plan v2 (Local-First)

> Everything runs on the team's laptop. No shared backend. No deployment. No OAuth for builders.

---

## Architecture

```
Team's laptop:
├── Next.js frontend        (localhost:3000)
├── FastAPI backend          (localhost:8000)
├── SQLite                   (hackathon.db)
└── .env
      SHOPIFY_ACCESS_TOKEN=shpat_xxxxx   ← pre-captured by Albert
      SHOPIFY_STORE_URL=gzh-07.myshopify.com
```

One repo. One command: `npm run dev`. Starts both frontend and backend.
Multiple team members can clone the same fork, use the same token — no conflicts.

---

## What Changes from v1

| v1 (shared backend) | v2 (local-first) |
|---|---|
| Hosted FastAPI on Render | Local FastAPI on localhost:8000 |
| PostgreSQL | SQLite (zero config) |
| Multi-tenant (API key → store routing) | Single store (token in .env) |
| OAuth redirect needed at install | Tokens pre-captured by Albert |
| Teams hit remote REST API | Teams hit their own localhost |
| Order simulator runs centrally | Order simulator runs locally |
| Complex deployment | `npm run dev` and done |

---

## Repo Structure

```
HackathonStarterRepo/
├── CLAUDE.md                        ← The brain (updated for local arch)
├── .env.example                     ← ACCESS_TOKEN + STORE_URL
├── package.json                     ← Root: `npm run dev` starts everything
├── README.md
│
├── backend/                         ← FastAPI (runs on localhost:8000)
│   ├── app/
│   │   ├── main.py                  ← FastAPI entry, CORS, lifespan
│   │   ├── config.py                ← Reads .env (token, store URL)
│   │   ├── database.py              ← SQLite + SQLAlchemy async (aiosqlite)
│   │   ├── models.py                ← Product, Order, Customer, Event (single file)
│   │   ├── shopify.py               ← Shopify REST + GraphQL client
│   │   ├── sync.py                  ← Data sync (products, orders, customers)
│   │   ├── simulator.py             ← Order simulator (creates fake orders)
│   │   └── routers/
│   │       ├── store.py             ← GET /store
│   │       ├── products.py          ← GET /products, GET /products/:id
│   │       ├── orders.py            ← GET /orders, GET /orders/:id
│   │       ├── customers.py         ← GET /customers
│   │       ├── inventory.py         ← GET /inventory
│   │       ├── analytics.py         ← GET /analytics/revenue, /top-products, etc.
│   │       ├── events.py            ← GET /events/stream (SSE), GET /events/history
│   │       ├── actions.py           ← POST /orders/draft, POST /discounts, POST /email
│   │       └── shopify_proxy.py     ← POST /shopify/graphql (passthrough)
│   ├── requirements.txt             ← FastAPI, uvicorn, sqlalchemy, aiosqlite, httpx
│   └── seed.py                      ← Loads curated product catalog into store
│
├── frontend/                        ← Next.js 14 (runs on localhost:3000)
│   ├── (same as v1 — components, hooks, pages, lib)
│   └── lib/constants.ts             ← API_BASE = localhost:8000
│
├── docs/
│   ├── IDEAS.md
│   └── API.md
│
└── scripts/
    └── capture-tokens.py            ← Albert runs this pre-event to get access tokens
```

---

## Key Simplifications

### 1. Single-file models (no migrations)
SQLite + `create_all()` on startup. No Alembic. No migration headaches.

```python
# backend/app/database.py
engine = create_async_engine("sqlite+aiosqlite:///./hackathon.db")

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
```

### 2. No auth middleware
No API keys, no JWT, no X-Team-Key header. The backend reads the Shopify token from .env and uses it directly. Every endpoint is open on localhost.

### 3. Flat backend structure
Instead of core/, models/, schemas/, services/, repositories/ — just flat files:
- `models.py` — all SQLAlchemy models
- `shopify.py` — all Shopify API calls
- `sync.py` — data sync logic
- `routers/` — endpoint files

Builders can read the entire backend in 5 minutes.

### 4. Root package.json starts everything
```json
{
  "scripts": {
    "dev": "concurrently \"cd backend && uvicorn app.main:app --reload --port 8000\" \"cd frontend && npm run dev\"",
    "setup": "cd frontend && npm install && cd ../backend && pip install -r requirements.txt",
    "sync": "cd backend && python -m app.sync"
  }
}
```

### 5. Auto-sync on startup
When backend starts, it checks if hackathon.db has data. If empty, triggers a full sync from Shopify. Teams see data within 30 seconds of first `npm run dev`.

### 6. SQLite for everything
- Zero config
- File-based (hackathon.db appears in project root)
- Multiple team members can read simultaneously
- Using aiosqlite for async compat with FastAPI
- If they want to inspect data: `sqlite3 hackathon.db ".tables"`

---

## Token Capture Script (Albert runs pre-event)

`scripts/capture-tokens.py` — A local OAuth handler:

1. Starts a Flask/FastAPI server on localhost:3456
2. For each app (gzh-01 through gzh-30):
   a. Opens the Shopify install URL in the browser
   b. Albert clicks "Install" in the Shopify admin
   c. Shopify redirects to localhost:3456/auth/callback with auth code
   d. Script exchanges code for permanent access token
   e. Saves token to `tokens.json`
3. After all 30: outputs a clean JSON mapping

```json
{
  "gzh-01": {
    "store": "gzh-01.myshopify.com",
    "access_token": "shpat_xxxxx",
    "client_id": "your_client_id_here",
    "api_secret": "your_app_secret_here"
  },
  ...
}
```

Each team card gets their access_token + store URL from this file.

### Prerequisites
- Must update all 30 apps' `application_url` to `http://localhost:3456`
  and `redirect_urls` to `["http://localhost:3456/auth/callback"]`
- OR: use a separate TOML deploy to set these temporarily, then revert after

### Alternative: Use Shopify CLI
```bash
# For each app:
shopify app dev --store gzh-01.myshopify.com --client-id <id>
# This handles OAuth and creates a session
# Extract token from the session store
```

---

## Seed Script (loads real product catalog)

`backend/seed.py` — Runs against each store via Shopify Admin API:

Loads a curated DTC brand catalog instead of snowboards:
- 50 products across 5 collections (Best Sellers, New Arrivals, Sale, Core, Limited Edition)
- Realistic pricing ($19–$299)
- Multiple variants (sizes, colors)
- Product images (from Shopify's free stock or placeholder URLs)
- 30 customer profiles with varied attributes
- 10 discount codes (WELCOME10, FLASH20, VIP30, etc.)

Albert runs this once per store after capturing tokens:
```bash
python backend/seed.py --tokens tokens.json --all
```

---

## Order Simulator (local)

Runs as a background task inside the FastAPI app. On startup:
- Picks random products from SQLite
- Creates orders on Shopify via REST API every 60-180 seconds
- Shopify processes the order → data becomes available
- Next sync pulls it into SQLite
- SSE pushes event to frontend

Builders see live orders appearing on their dashboard.

Can be toggled: `SIMULATOR_ENABLED=true` in .env (default: true).

---

## Builder Experience

```
0:00  Get credential card. Fork repo. Clone.
0:02  cp .env.example .env → paste token + store URL
0:03  npm run setup (installs frontend + backend deps)
0:05  npm run dev
      → Backend starts, detects empty DB, auto-syncs from Shopify
      → Frontend starts on :3000
0:06  Open localhost:3000 → working dashboard with real store data
0:08  Open Claude Code. Type what you want to build.
0:40  Core feature done. Polish time.
4:00  Demo: turn laptop to judges, show localhost:3000
```

---

## Build Order

### Day 1 (Today, Tue): Restructure + Backend
- [ ] Restructure repo (move pipe/ → backend/, flatten)
- [ ] Rewrite backend for single-tenant SQLite
- [ ] Strip multi-store routing, API key auth
- [ ] Add auto-sync on startup
- [ ] Add order simulator
- [ ] Root package.json with concurrently
- [ ] Test: `npm run dev` starts both servers

### Day 2 (Wed): Token Capture + Seed
- [ ] Build token capture script
- [ ] Update all 30 apps' redirect URLs (TOML deploy)
- [ ] Run capture: get 30 access tokens
- [ ] Build seed script (curated product catalog)
- [ ] Seed all 30 stores
- [ ] Start simulator on admin test store, verify orders flowing

### Day 3 (Thu): Frontend + CLAUDE.md + Polish
- [ ] Update frontend to point to localhost:8000
- [ ] Update CLAUDE.md for local architecture
- [ ] Update README, .env.example, docs
- [ ] End-to-end test: fresh clone → working dashboard
- [ ] Generate credential cards
- [ ] Push to GitHub

### Day 4 (Fri): Final Verification
- [ ] Fresh machine test (or fresh user account)
- [ ] Test with 2 people using same token simultaneously
- [ ] Test Claude Code: paste an example prompt, verify it builds correctly
- [ ] Print credential cards
- [ ] Sleep

---

## Credential Card (per team)

```
┌──────────────────────────────────┐
│  TEAM 07 — SHOPIFY HACKATHON     │
│                                  │
│  Store: gzh-07.myshopify.com     │
│  Token: shpat_xxxxxxxxxxxxxxx    │
│                                  │
│  1. Fork the repo                │
│  2. cp .env.example .env         │
│  3. Paste your token + store     │
│  4. npm run setup                │
│  5. npm run dev                  │
│  6. Open localhost:3000          │
│  7. Open Claude Code and build!  │
│                                  │
│  WiFi: HackathonNet / hack2026   │
│  Help: find Albert               │
└──────────────────────────────────┘
```

---

## Open Questions

1. **Seed data theme** — DTC fashion brand? Tech accessories? Skincare? Something that photographs well for demos.
2. **Simulator rate** — 1 order per 60-180s feels right? Too fast and SQLite might lag. Too slow and data feels static.
3. **Python version** — Assume Python 3.10+? Most devs will have it. Include a check in setup.
4. **npm run dev prerequisite** — Need both Node 18+ and Python 3.10+. Add a preflight check script?
5. **Multiple instances** — If 2 team members both run the backend with simulator, they'll create double orders. Add a file lock or just document "only one person runs the backend"?
