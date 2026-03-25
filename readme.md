# Shopify App Hackathon — Starter Repo

Build a Shopify app in 4 hours. Everything hard is already done.

## Quick Start

```bash
# 1. Fork this repo, then clone your fork
git clone https://github.com/YOUR_USERNAME/HackathonStarterRepo.git
cd HackathonStarterRepo

# 2. Set your credentials (from your team card)
cp .env.example .env
# Edit .env — paste your TEAM_API_KEY and STORE_URL

# 3. Install and run
cd frontend
npm install
npm run dev

# 4. Open http://localhost:3000
# You should see a working dashboard with live data
```

## What You Get

- **Working dashboard** with KPIs, charts, product table, and live order feed
- **Real Shopify store** with products, customers, and orders
- **Live data** — new orders arrive every 30-120 seconds
- **Full API access** — read/write products, orders, customers, inventory, storefront
- **Pre-built components** — charts, tables, cards, modals, badges
- **Claude Code ready** — CLAUDE.md has everything Claude needs to build features from natural language

## Your Store

| What | Where |
|------|-------|
| Dashboard | http://localhost:3000 |
| Store Admin | https://YOUR-STORE.myshopify.com/admin |
| Storefront | https://YOUR-STORE.myshopify.com |

Credentials are on your team card.

## Build Something

Open Claude Code in this repo and try:

> "Create a page that predicts when each product will go out of stock based on sales velocity"

> "Build a customer segmentation view using RFM analysis with a donut chart"

> "Add a live anomaly detector that flags unusual order patterns"

See `CLAUDE.md` for the full API reference, component library, and more example prompts.
See `docs/IDEAS.md` for 10 build ideas with difficulty ratings.

## Project Structure

```
frontend/           ← You work here
├── pages/          ← Add new pages (auto-routed)
├── components/     ← Charts, tables, cards, layout
├── hooks/          ← Data fetching hooks
├── lib/            ← API client, types, utilities
└── styles/         ← Tailwind dark theme

pipe/               ← Shared backend (deployed for you, don't modify)
docs/               ← API reference + build ideas
CLAUDE.md           ← The brain — Claude Code reads this
```

## Tech Stack

- **Frontend**: Next.js 14, TypeScript, Tailwind CSS
- **Backend**: FastAPI + PostgreSQL (shared, hosted for you)
- **Store**: Shopify Dev Store with full API access
- **Real-time**: Server-Sent Events for live order updates

---

Built with Growzilla for the Claude × Shopify Hackathon.
