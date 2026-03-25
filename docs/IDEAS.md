# Hackathon Build Ideas

10 project ideas organized by difficulty. Each includes a ready-to-paste Claude Code prompt.
Pick one, paste the prompt, and start building.

---

## Easy (1-2 hours)

### 1. Smart Dashboard
Enhanced KPIs with trend analysis, forecasting, and product performance scoring.

**Data**: `api.getRevenue('30d')`, `api.getTopProducts(10)`, `api.getStore()`, `api.getOrders()`
**Build**: KPICards with Sparklines, LineChart for revenue trends, BarChart for product rankings, simple linear trend projection
**Stretch**: Add period comparison (this week vs last week), export KPIs as PNG

**Claude Code prompt:**
```
Create an enhanced dashboard at /smart-dashboard. Fetch revenue data for 7d and 30d using api.getRevenue(). Show 6 KPICards: Total Revenue (with Sparkline of daily values), Orders Today, Average Order Value, Revenue Growth % (compare last 7d vs prior 7d), Top Product revenue, Customer Count. Below the KPIs, show a LineChart of 30-day revenue with a simple trend line (linear regression). Below that, a BarChart of top 10 products by revenue. Use the Shell component and follow the dark theme design rules.
```

---

### 2. Inventory Sentinel
Stockout prediction with email alerts and reorder suggestions.

**Data**: `api.getInventory()`, `api.getOrders()`, `api.sendEmail()`
**Build**: DataTable with stock levels, calculated sales velocity, days-until-stockout, color-coded urgency
**Stretch**: Automated email alerts when stock drops below threshold, reorder quantity suggestions

**Claude Code prompt:**
```
Create a page at /inventory that shows stockout predictions. Fetch inventory with api.getInventory() and recent orders with api.getOrders({ limit: 200 }). For each product, calculate 7-day sales velocity by counting units sold from order line_items in the last 7 days. Compute days_until_stockout = current_quantity / daily_velocity. Display a DataTable with columns: Product, Variant, Current Stock, Daily Velocity, Days Until Stockout, Status. Color-code the Status column: red Badge "Critical" for < 3 days, yellow Badge "Warning" for < 7 days, green Badge "Healthy" for >= 7 days. Sort by days_until_stockout ascending (most urgent first). Add a KPICard row at top showing: Total SKUs, Critical Count, Warning Count, Healthy Count. When a user clicks a row, show a Modal with a LineChart projecting that product's inventory depletion over the next 30 days.
```

---

### 3. Customer DNA
RFM segmentation with customer profiles and segment visualization.

**Data**: `api.getCustomers()`, `api.getOrders()`
**Build**: DonutChart of segments, DataTable of customers with scores, segment detail cards
**Stretch**: Per-customer detail modal, auto-generate discount codes for at-risk customers

**Claude Code prompt:**
```
Build a page at /customers/segments that performs RFM analysis. Fetch all customers with api.getCustomers({ limit: 500 }) and all orders with api.getOrders({ limit: 500 }). For each customer, calculate: Recency = days since last_order_at (lower is better), Frequency = orders_count, Monetary = total_spent. Score each dimension 1-5 using quintiles (split into 5 equal groups). Define segments: Champions (R>=4 AND F>=4 AND M>=4), Loyal Customers (F>=3 AND M>=3), At Risk (R<=2 AND F>=3), New Customers (orders_count <= 1 AND recency < 30), Lost (R<=2 AND F<=2). Show a DonutChart with segment distribution (use distinct colors: green Champions, blue Loyal, orange At Risk, purple New, red Lost). Below it, show Tabs to switch between segments. Each tab shows a DataTable with: Customer Name, Email, Orders, Total Spent, Last Order, RFM Score. Add 4 KPICards at top: Total Customers, Champions Count, At Risk Count, Average Lifetime Value.
```

---

## Medium (2-3 hours)

### 4. Store Detective
Order anomaly detection with fraud signals and real-time monitoring.

**Data**: `api.getHourlyPatterns()`, `api.getOrders()`, `useEventStream()`, `api.getRevenue('7d')`
**Build**: HeatMap of hourly patterns, anomaly alerts, suspicious order flagging, real-time deviation tracking
**Stretch**: Fraud scoring model (high value + new customer + unusual hour = suspicious), automatic email alerts

**Claude Code prompt:**
```
Create a page at /detective that detects order anomalies. First, fetch baseline patterns with api.getHourlyPatterns() to get average orders per hour. Fetch today's orders with api.getOrders({ since: new Date().toISOString().split('T')[0] }). Group today's orders by hour and compare each hour's count against the baseline average. Calculate standard deviation for each hour from the baseline. Flag any hour where actual orders deviate by more than 2 standard deviations as an anomaly. Show: (1) A HeatMap with 24 columns (hours) showing expected vs actual volume (two rows). (2) A KPICard row: Orders Today, vs Expected, Deviation %, Anomalies Detected. (3) A "Suspicious Orders" DataTable that flags orders where: total_price > 3x average order value, OR order placed between midnight-5am, OR new customer (orders_count=1) with high value. Give each order a risk score 0-100. (4) Use useEventStream() to show new orders arriving in a LiveFeed at the bottom, highlighting any that match suspicious criteria with a red Badge. Sort suspicious orders by risk score descending.
```

---

### 5. Price Oracle
Dynamic pricing suggestions based on demand patterns, velocity, and inventory pressure.

**Data**: `api.getProducts()`, `api.getOrders()`, `api.getInventory()`, `api.getTopProducts(50)`
**Build**: Product pricing dashboard, demand elasticity estimation, price suggestion engine, revenue impact projections
**Stretch**: A/B price testing via discount codes, competitor price tracking mockup

**Claude Code prompt:**
```
Create a page at /pricing that suggests optimal prices. Fetch products with api.getProducts({ limit: 100 }), inventory with api.getInventory(), and recent orders with api.getOrders({ limit: 500 }). For each product, calculate: (1) sales_velocity = units sold per day over last 14 days, (2) inventory_days = current stock / daily velocity, (3) demand_score = normalize velocity 0-100 across all products. Generate pricing suggestions: if demand_score > 75 AND inventory_days < 14, suggest price increase of 10-20% ("High demand, limited stock"); if demand_score < 25 AND inventory_days > 30, suggest price decrease of 10-15% ("Low demand, excess stock"); otherwise "Price is appropriate". Show a DataTable with: Product, Current Price, Velocity, Stock Days, Demand Score, Suggested Price, Suggested Change %, Reason. Add KPICards: Products Analyzed, Suggested Increases, Suggested Decreases, Projected Revenue Impact (sum of price changes * projected units). Add a BarChart showing top 10 products by potential revenue uplift. Color-code suggestions: green for increase, red for decrease, gray for no change.
```

---

### 6. Fulfillment Brain
Smart fulfillment prioritization with shipping optimization and delivery predictions.

**Data**: `api.getOrders()`, `api.getProducts()`, `api.getInventory()`, `useEventStream()`
**Build**: Priority queue of unfulfilled orders, scoring algorithm, batch fulfillment suggestions, real-time order intake
**Stretch**: Estimated shipping cost calculator, regional grouping for batch shipments

**Claude Code prompt:**
```
Create a page at /fulfillment that prioritizes order fulfillment. Fetch orders with api.getOrders({ status: 'unfulfilled', limit: 200 }) and inventory with api.getInventory(). Score each unfulfilled order for priority: +30 points if order is > 24 hours old, +20 if total_price > average order value, +15 if customer is returning (orders_count > 1), +10 if all items are in stock, -20 if any item is out of stock. Show: (1) KPICards: Unfulfilled Orders, Ready to Ship (all items in stock), Blocked (out of stock items), Average Wait Time. (2) A DataTable sorted by priority score descending with columns: Order #, Customer, Items, Total, Age (hours), Priority Score, Status (Ready/Blocked Badge). Clicking a row opens a Modal showing line items with stock availability for each. (3) A "Batch Fulfillment" section: group ready-to-ship orders and show a Button "Fulfill Top 10" that would process them. (4) Use useEventStream() to show new incoming orders in a small LiveFeed sidebar, auto-adding them to the priority queue. (5) A BarChart showing orders by age bucket: 0-2h, 2-6h, 6-12h, 12-24h, 24h+.
```

---

## Hard (3-4 hours)

### 7. Demand Prophet
Time-series forecasting with seasonality modeling, trend decomposition, and inventory optimization.

**Data**: `api.getRevenue('90d')`, `api.getOrders({ limit: 1000 })`, `api.getTopProducts(20)`, `api.getInventory()`
**Build**: Revenue forecasting with trend + seasonality decomposition, per-product demand curves, reorder point calculator, confidence intervals
**Stretch**: Promotion impact simulator (what if we run a 20% sale?), automatic reorder email triggers

**Claude Code prompt:**
```
Create a page at /forecast with demand forecasting. Fetch 90-day revenue with api.getRevenue('90d') and orders with api.getOrders({ limit: 1000 }). Implement time-series analysis: (1) Calculate 7-day moving average to smooth noise. (2) Detect trend using linear regression on the smoothed series. (3) Calculate day-of-week seasonality indices (average each weekday's deviation from trend). (4) Project next 30 days: for each future day, predicted = trend_value * seasonality_index_for_weekday. (5) Calculate 80% confidence interval using historical residual standard deviation. Show: a LineChart with three series — actual (solid green), moving average (solid white), forecast (dashed green), confidence band (shaded). KPICards: Projected 30-Day Revenue, Daily Growth Rate, Best Day of Week, Worst Day of Week. A second section with per-product forecasting: DataTable of top 20 products with columns: Product, Current Velocity, Projected 30-Day Units, Current Stock, Reorder Date (when stock hits 0), Reorder Quantity (30 days of stock). Add Tabs to switch between Revenue view and Product view. Use DateRange to let the user choose the analysis period.
```

---

### 8. Customer Journey AI
Path analysis from landing_site/referring_site data, conversion funnels, and traffic source attribution.

**Data**: `api.getOrders({ limit: 1000 })`, `api.getCustomers()`, `api.getRevenue('30d')`
**Build**: Traffic source breakdown, referring site analysis, landing page performance, customer acquisition cost proxy, conversion funnel
**Stretch**: Multi-touch attribution model, cohort comparison by source, customer journey visualization

**Claude Code prompt:**
```
Create a page at /journeys that analyzes customer acquisition paths. Fetch orders with api.getOrders({ limit: 1000 }) and customers with api.getCustomers({ limit: 500 }). From orders, extract and normalize referring_site (group by domain: google.com, facebook.com, instagram.com, direct, etc.) and landing_site (group by path: /, /products/*, /collections/*, etc.). Build: (1) DonutChart of order distribution by traffic source (referring_site domains). (2) BarChart of revenue by traffic source. (3) DataTable of traffic sources with columns: Source, Orders, Revenue, AOV, New Customers %, Returning %. (4) A "Landing Pages" section: BarChart of top 10 landing pages by conversion volume. (5) A "Customer Paths" section: for returning customers, show their order sequence — what source brought them first vs what brought them back. Display as a simple flow: First Visit Source → Repeat Visit Source, with counts. (6) KPICards: Total Traffic Sources, Top Source by Revenue, Highest AOV Source, New Customer Rate. Add Tabs to switch between Sources view, Landing Pages view, and Customer Paths view. Use Select to filter by date range.
```

---

### 9. AI Store Clerk
Storefront product recommendation widget using purchase co-occurrence and browsing affinity.

**Data**: `api.getOrders({ limit: 1000 })`, `api.getProducts()`, `api.injectStorefrontScript()`
**Build**: Product co-occurrence matrix from order data, recommendation engine, storefront JS widget that shows "Frequently Bought Together"
**Stretch**: Personalized recommendations per customer, "Trending Now" widget, A/B test different recommendation algorithms

**Claude Code prompt:**
```
Build a product recommendation system with two parts. PART 1 — Admin page at /recommendations: Fetch orders with api.getOrders({ limit: 1000 }). Build a co-purchase matrix: for every pair of products that appear in the same order, count co-occurrences. For each product, find its top 5 most frequently co-purchased products. Show a DataTable: Product, Top 3 Recommendations, Co-purchase Score. Add a product selector (Select component) — when you pick a product, show its full recommendation list with scores in a Card. Show a HeatMap of the top 20 products' co-purchase relationships. PART 2 — Storefront widget: Create public/recommendations-widget.js. This script: (a) detects the current product page from the URL or page DOM, (b) fetches the co-purchase data from a JSON file you generate at public/recommendations.json, (c) injects a "Frequently Bought Together" section below the product description showing the top 3 recommended products with images, titles, and prices, (d) styled to match a clean Shopify theme (white background, grid layout, "Add to Cart" buttons). On the admin page, add a Button "Generate & Deploy Widget" that: builds the recommendations.json from current data and calls api.injectStorefrontScript() to install the widget. Include instructions to visit the store URL to see it live.
```

---

### 10. Revenue Autopilot
End-to-end autonomous system: predict demand, create discounts for slow movers, suggest reorders for fast movers, email alerts.

**Data**: All endpoints — `api.getRevenue('90d')`, `api.getOrders()`, `api.getProducts()`, `api.getInventory()`, `api.getCustomers()`, `api.createDiscount()`, `api.sendEmail()`, `useEventStream()`
**Build**: Unified command center with forecasting, automated discount creation, reorder alerts, customer re-engagement emails, real-time monitoring
**Stretch**: Fully autonomous mode that runs all actions without confirmation, ROI tracking dashboard

**Claude Code prompt:**
```
Create a Revenue Autopilot command center at /autopilot. This page combines forecasting, automation, and alerts into one view. Build 4 sections using Tabs:

TAB 1 — "Forecast": Fetch api.getRevenue('90d') and api.getOrders({ limit: 500 }). Show a LineChart of revenue with 30-day linear projection. KPICards: Projected Monthly Revenue, Growth Rate, Best Product, Worst Product.

TAB 2 — "Slow Movers": Identify products with declining sales velocity (compare last 7 days vs prior 7 days). Show a DataTable: Product, Current Velocity, Velocity Change %, Current Stock, Days of Stock. For each slow mover, calculate a suggested discount (10% if velocity dropped 20-50%, 20% if dropped >50%). Add a Button per row "Create Discount" that calls api.createDiscount() with an auto-generated code like "MOVE-{product_handle}-{percentage}". Show success/failure status.

TAB 3 — "Fast Movers": Products with increasing velocity AND stock dropping below 14 days. DataTable: Product, Velocity, Stock Days, Reorder Urgency (Critical/Warning/OK). Button "Send Reorder Alert" that calls api.sendEmail() to send a reorder notification with product details and suggested quantity (30 days of stock at current velocity).

TAB 4 — "Live Monitor": Use useEventStream() to show real-time orders. Running KPICards that update live: Orders This Hour, Revenue This Hour, vs Forecast. Highlight any order that triggers an alert (large order, low-stock product purchased, returning champion customer). Auto-send email alerts for critical inventory events.

Add a master KPICard row at the top (visible on all tabs): Total Revenue (30d), Active Discounts, Reorder Alerts Sent, Anomalies Today.
```

---

## Tips for All Ideas
- Start with the Claude Code prompt as-is. It will build 80% of the feature.
- Then iterate: "Make the table sortable by the Score column" or "Add a filter for date range"
- Use `useEventStream()` to make anything feel alive — real-time data is your superpower
- The store has real products with images, real customers with history, and orders flowing in constantly
- You can write to the store: create discounts, send emails, inject widgets into the storefront
- Check the CLAUDE.md for the full API reference and component list
