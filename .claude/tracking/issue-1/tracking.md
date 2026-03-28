# Issue #1: Shopify Hackathon — AutoPilot AI Agents

## Status: dev/implement
## Branch: `issue-1-shopify-autopilot`

## Definition of Done

- [ ] `intelligence.ts` scores products into 4 tiers with velocity + stockout prediction
- [ ] Autopilot page renders 4 agent cards with live status
- [ ] Inventory tab shows scored/tiered products in DataTable
- [ ] At least 2 autonomous actions fire (discount creation + email alert)
- [ ] Storefront widget deployed via `injectStorefrontScript()` and visible on store
- [ ] Customer segments page with DonutChart + DataTable
- [ ] Daily insight card renders with rotating merchandising tip
- [ ] Shell nav updated with new pages
- [ ] All pages handle loading/empty states

## Acceptance Criteria

### AC1: Intelligence Layer
- `scoreProducts()` accepts Shopify products + orders + inventory
- Outputs scored items with: score 0-100, tier (Core/Strong/Slow/Exit), velocity, daysLeft, trend
- Uses Plus2's power-scale algorithm (`(value/max)^0.25 * 100`)
- Tier thresholds: Core 70+, Strong 55-69, Slow 40-54, Exit 0-39

### AC2: Autopilot Page — Agents Tab
- 4 agent cards: Rick (Ops), Hank (Supply Chain), Ron (Finance), Marcus (Chief of Staff)
- Each shows: name, emoji, domain, status indicator, last action, action count
- Live activity feed below cards, timestamped and tagged by agent

### AC3: Autopilot Page — Inventory Tab
- DataTable with columns: Product, Score (color bar), Tier (badge), Stock, Velocity, Days Left, Trend
- KPICards: Total SKUs, Critical (<3 days), Warning (<7 days), Healthy
- Sorted by urgency (days-until-stockout ascending)

### AC4: Autopilot Page — Actions Tab
- Log of autonomous actions: discounts created, emails sent, widgets deployed
- Each with: timestamp, agent name, action type, details, status

### AC5: Autopilot Page — Live Tab
- useEventStream() powering LiveFeed
- KPICards: Orders This Hour, Revenue This Hour
- Incoming orders trigger score check → flash alert if low-stock product

### AC6: Autonomous Actions
- Rick: stockout alert emails for products <3 days stock
- Ron: clearance discounts for slow movers (velocity declining + excess stock)
- Marcus: deploys storefront widget, generates daily insight
- All agents use hasActed map to prevent duplicate actions

### AC7: Customer Segments Page
- RFM scoring: Recency, Frequency, Monetary (1-5 quintiles)
- Segments: Champions, Loyal, At Risk, New, Lost
- DonutChart of segment distribution
- DataTable with customer details + segment + scores
- KPICards: Total Customers, Champions, At Risk, Avg LTV

### AC8: Daily Insight Card
- Emerald-green card at top of autopilot page
- Rotates daily from pre-written merchandising insights
- Adapted from Plus2's Pickle of the Day

### AC9: Storefront Widget
- `public/low-stock-widget.js` — vanilla JS
- Shows "Only X left!" badge on product pages for items with <10 stock
- Injected via `api.injectStorefrontScript()`

### AC10: Navigation
- Shell.tsx updated with Autopilot and Segments nav items

## Files to Create/Modify

| File | Action |
|------|--------|
| `frontend/lib/intelligence.ts` | CREATE |
| `frontend/lib/agents/types.ts` | CREATE |
| `frontend/lib/agents/rick.ts` | CREATE |
| `frontend/lib/agents/hank.ts` | CREATE |
| `frontend/lib/agents/ron.ts` | CREATE |
| `frontend/lib/agents/marcus.ts` | CREATE |
| `frontend/pages/autopilot.tsx` | CREATE |
| `frontend/pages/segments.tsx` | CREATE |
| `frontend/components/AgentCard.tsx` | CREATE |
| `frontend/components/ActionLog.tsx` | CREATE |
| `frontend/components/DailyInsight.tsx` | CREATE |
| `frontend/public/low-stock-widget.js` | CREATE |
| `frontend/components/Shell.tsx` | MODIFY |

## Build Order

1. **Phase 1** — `intelligence.ts` + `agents/types.ts` (foundation)
2. **Phase 2** — Agent modules (`rick.ts`, `hank.ts`, `ron.ts`, `marcus.ts`)
3. **Phase 3** — UI components (`AgentCard`, `ActionLog`, `DailyInsight`)
4. **Phase 4** — Pages (`autopilot.tsx`, `segments.tsx`)
5. **Phase 5** — Storefront widget + Shell nav update
6. **Phase 6** — Wire up agent loop in autopilot page
