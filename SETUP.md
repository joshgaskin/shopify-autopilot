# Setup Guide

## Prerequisites
- Node.js 18+
- Python 3.10+
- pip (Python package manager)

## Steps

### 1. Copy environment file
```bash
cp .env.example .env
```

### 2. Add your credentials
Open `.env` and paste your team credentials from your card:
```
SHOPIFY_ACCESS_TOKEN=shpat_your_token_here
SHOPIFY_STORE_URL=gzh-XX.myshopify.com
```

### 3. Install dependencies
```bash
npm run setup
```
This installs both frontend (Node) and backend (Python) dependencies.

### 4. Start the app
```bash
npm run dev
```
This starts:
- Backend API at http://localhost:8000
- Frontend dashboard at http://localhost:3000

On first start, the backend automatically syncs your store's products, orders, and customers into a local SQLite database. This takes ~30 seconds.

### 5. Open your dashboard
Go to http://localhost:3000 — you should see a working dashboard with your store's real data.

## What's Running

| Service | URL | What it does |
|---------|-----|-------------|
| Frontend | http://localhost:3000 | Next.js dashboard — this is what you build |
| Backend API | http://localhost:8000 | FastAPI — fetches & caches Shopify data locally |
| API docs | http://localhost:8000/docs | Auto-generated API docs (Swagger) |

## Team Setup

**One person** on the team runs the backend (with simulator). Other team members can:
- Clone the same fork and run `npm run dev` — they'll have their own local copy
- Or pair program on one machine

**Important**: If multiple people run the backend with `SIMULATOR_ENABLED=true`, you'll get double orders. Only ONE person should have the simulator on. Others set `SIMULATOR_ENABLED=false` in their `.env`.

## Troubleshooting

| Problem | Fix |
|---------|-----|
| "Module not found" | Run `npm run setup` again |
| Backend won't start | Check Python 3.10+: `python3 --version` |
| No data on dashboard | Wait 30s for initial sync, or run `npm run sync` |
| "Invalid API key" | Check SHOPIFY_ACCESS_TOKEN in .env matches your card |
| Port 3000 in use | Kill other dev servers: `lsof -i :3000` then `kill <PID>` |
| Port 8000 in use | Kill other python processes: `lsof -i :8000` then `kill <PID>` |

## Next Steps
1. Read `CLAUDE.md` — it has the full API reference and example prompts
2. Read `docs/IDEAS.md` — 10 build ideas with difficulty ratings
3. Open Claude Code and start building!
