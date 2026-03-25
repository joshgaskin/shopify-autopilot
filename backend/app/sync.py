"""
Data sync — pulls products, orders, customers from Shopify
and upserts them into local SQLite.

No multi-tenant. No store_id. Just one store.
"""
import json
import logging
from datetime import datetime, timezone

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.events import EventManager
from app.shopify import ShopifyClient, ShopifyAPIError

logger = logging.getLogger(__name__)


async def sync_all(db: AsyncSession, client: ShopifyClient) -> dict[str, int]:
    """Full sync: products, orders, customers. Returns counts."""
    logger.info("Starting full sync from Shopify...")

    products = await sync_products(db, client)
    logger.info("Synced %d products", products)

    orders = await sync_orders(db, client)
    logger.info("Synced %d orders", orders)

    customers = await sync_customers(db, client)
    logger.info("Synced %d customers", customers)

    await EventManager.get().publish("sync.completed", {
        "products": products,
        "orders": orders,
        "customers": customers,
    })

    return {"products": products, "orders": orders, "customers": customers}


async def sync_products(db: AsyncSession, client: ShopifyClient) -> int:
    """Fetch all products and upsert into SQLite."""
    count = 0
    cursor = None
    now = datetime.now(timezone.utc).isoformat()

    while True:
        data = await client.get_products(cursor=cursor)
        products_data = data.get("products", {})
        edges = products_data.get("edges", [])
        if not edges:
            break

        for edge in edges:
            node = edge["node"]
            cursor = edge["cursor"]

            price_range = node.get("priceRangeV2", {})
            price_min = float(
                price_range.get("minVariantPrice", {}).get("amount", 0)
            )
            price_max = float(
                price_range.get("maxVariantPrice", {}).get("amount", 0)
            )
            collections = [
                e["node"]["title"]
                for e in node.get("collections", {}).get("edges", [])
            ]
            variants = [
                {
                    "id": v["node"]["id"],
                    "title": v["node"]["title"],
                    "sku": v["node"].get("sku", ""),
                    "price": v["node"].get("price", "0"),
                    "inventory_quantity": v["node"].get("inventoryQuantity", 0),
                }
                for v in node.get("variants", {}).get("edges", [])
            ]
            featured = node.get("featuredImage")
            image_url = featured["url"] if featured else None

            # SQLite upsert via INSERT OR REPLACE
            await db.execute(
                text("""
                    INSERT OR REPLACE INTO products
                        (id, title, handle, status, product_type, vendor,
                         price_min, price_max, variants, collections,
                         featured_image_url, inventory_total, created_at, updated_at)
                    VALUES
                        (:id, :title, :handle, :status, :product_type, :vendor,
                         :price_min, :price_max, :variants, :collections,
                         :featured_image_url, :inventory_total, :created_at, :updated_at)
                """),
                {
                    "id": node["id"],
                    "title": node.get("title", ""),
                    "handle": node.get("handle", ""),
                    "status": node.get("status", "ACTIVE").lower(),
                    "product_type": node.get("productType"),
                    "vendor": node.get("vendor"),
                    "price_min": price_min,
                    "price_max": price_max,
                    "variants": json.dumps(variants),
                    "collections": json.dumps(collections),
                    "featured_image_url": image_url,
                    "inventory_total": node.get("totalInventory", 0),
                    "created_at": now,
                    "updated_at": now,
                },
            )
            count += 1

        page_info = products_data.get("pageInfo", {})
        if not page_info.get("hasNextPage"):
            break

    await db.flush()
    return count


async def sync_orders(db: AsyncSession, client: ShopifyClient) -> int:
    """Fetch all orders and upsert into SQLite."""
    count = 0
    cursor = None

    while True:
        data = await client.get_orders(cursor=cursor)
        orders_data = data.get("orders", {})
        edges = orders_data.get("edges", [])
        if not edges:
            break

        for edge in edges:
            node = edge["node"]
            cursor = edge["cursor"]

            total_price = float(
                node.get("totalPriceSet", {}).get("shopMoney", {}).get("amount", 0)
            )
            subtotal_price = float(
                node.get("subtotalPriceSet", {}).get("shopMoney", {}).get("amount", 0)
            )
            total_tax = float(
                node.get("totalTaxSet", {}).get("shopMoney", {}).get("amount", 0)
            )
            total_discounts = float(
                node.get("totalDiscountsSet", {}).get("shopMoney", {}).get("amount", 0)
            )
            currency = (
                node.get("totalPriceSet", {})
                .get("shopMoney", {})
                .get("currencyCode", "USD")
            )

            customer = node.get("customer") or {}
            customer_id = customer.get("id")
            customer_email = customer.get("email")
            customer_name = " ".join(
                filter(None, [customer.get("firstName"), customer.get("lastName")])
            ) or None

            line_items = []
            for li_edge in node.get("lineItems", {}).get("edges", []):
                li = li_edge["node"]
                line_items.append({
                    "id": li["id"],
                    "title": li["title"],
                    "quantity": li["quantity"],
                    "amount": float(
                        li.get("originalTotalSet", {})
                        .get("shopMoney", {})
                        .get("amount", 0)
                    ),
                    "variant_id": (li.get("variant") or {}).get("id"),
                    "product_id": (li.get("product") or {}).get("id"),
                })

            order_name = node.get("name", "#0")
            processed_at_str = node.get("processedAt", "")

            tags = node.get("tags", [])
            is_simulated = "simulated" in (
                tags if isinstance(tags, list) else tags.split(",")
            )

            await db.execute(
                text("""
                    INSERT OR REPLACE INTO orders
                        (id, order_number, total_price, subtotal_price,
                         total_discounts, total_tax, currency, financial_status,
                         fulfillment_status, line_items, customer_id, customer_email,
                         customer_name, discount_codes, landing_site, referring_site,
                         processed_at, created_at, is_simulated)
                    VALUES
                        (:id, :order_number, :total_price, :subtotal_price,
                         :total_discounts, :total_tax, :currency, :financial_status,
                         :fulfillment_status, :line_items, :customer_id,
                         :customer_email, :customer_name, :discount_codes,
                         :landing_site, :referring_site, :processed_at, :created_at,
                         :is_simulated)
                """),
                {
                    "id": node["id"],
                    "order_number": order_name,
                    "total_price": total_price,
                    "subtotal_price": subtotal_price,
                    "total_discounts": total_discounts,
                    "total_tax": total_tax,
                    "currency": currency,
                    "financial_status": (
                        node.get("financialStatus", "PENDING").lower()
                    ),
                    "fulfillment_status": (
                        (node.get("fulfillmentStatus") or "unfulfilled").lower()
                    ),
                    "line_items": json.dumps(line_items),
                    "customer_id": customer_id,
                    "customer_email": customer_email,
                    "customer_name": customer_name,
                    "discount_codes": json.dumps(node.get("discountCodes", [])),
                    "landing_site": node.get("landingSite", ""),
                    "referring_site": node.get("referringSite", ""),
                    "processed_at": processed_at_str,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "is_simulated": is_simulated,
                },
            )
            count += 1

        page_info = orders_data.get("pageInfo", {})
        if not page_info.get("hasNextPage"):
            break

    await db.flush()
    return count


async def sync_customers(db: AsyncSession, client: ShopifyClient) -> int:
    """Fetch all customers and upsert into SQLite."""
    count = 0
    cursor = None

    while True:
        data = await client.get_customers(cursor=cursor)
        customers_data = data.get("customers", {})
        edges = customers_data.get("edges", [])
        if not edges:
            break

        for edge in edges:
            node = edge["node"]
            cursor = edge["cursor"]

            total_spent = float(
                node.get("totalSpentV2", {}).get("amount", 0)
            )
            tags = node.get("tags", [])
            last_order = node.get("lastOrder")
            last_order_at = None
            if last_order and last_order.get("processedAt"):
                last_order_at = last_order["processedAt"]

            created_at = node.get("createdAt", datetime.now(timezone.utc).isoformat())

            await db.execute(
                text("""
                    INSERT OR REPLACE INTO customers
                        (id, email, first_name, last_name, orders_count,
                         total_spent, tags, created_at, last_order_at)
                    VALUES
                        (:id, :email, :first_name, :last_name, :orders_count,
                         :total_spent, :tags, :created_at, :last_order_at)
                """),
                {
                    "id": node["id"],
                    "email": node.get("email", ""),
                    "first_name": node.get("firstName", ""),
                    "last_name": node.get("lastName", ""),
                    "orders_count": node.get("ordersCount", 0),
                    "total_spent": total_spent,
                    "tags": json.dumps(tags if isinstance(tags, list) else []),
                    "created_at": created_at,
                    "last_order_at": last_order_at,
                },
            )
            count += 1

        page_info = customers_data.get("pageInfo", {})
        if not page_info.get("hasNextPage"):
            break

    await db.flush()
    return count


async def run_full_sync() -> dict[str, int]:
    """Standalone sync — used by `npm run sync` CLI command."""
    from app.database import init_db, get_db_context
    from app.config import get_settings

    await init_db()
    settings = get_settings()
    client = ShopifyClient(
        store_url=settings.SHOPIFY_STORE_URL,
        access_token=settings.SHOPIFY_ACCESS_TOKEN,
        api_version=settings.SHOPIFY_API_VERSION,
    )
    async with get_db_context() as db:
        result = await sync_all(db, client)
    await client.client.aclose()
    logger.info("Full sync complete: %s", result)
    return result
