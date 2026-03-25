"""
Order simulator — creates fake orders on the Shopify dev store.

Runs as a background asyncio task. Picks random products from local SQLite,
creates orders on Shopify via REST API, syncs back, and publishes events.
"""
import asyncio
import logging
import random
from datetime import datetime, timezone

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.config import get_settings
from app.events import EventManager
from app.models import Product, Order
from app.shopify import ShopifyClient

logger = logging.getLogger(__name__)

# Realistic fake customer names
FIRST_NAMES = [
    "Emma", "Liam", "Olivia", "Noah", "Ava", "Elijah", "Sophia", "James",
    "Isabella", "Oliver", "Mia", "Lucas", "Harper", "Mason", "Evelyn",
    "Logan", "Aria", "Alexander", "Luna", "Ethan",
]
LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller",
    "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez",
    "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin",
]
DISCOUNT_CODES = ["HACK10", "WELCOME15", "SAVE20", "DEMO25", "FIRST10"]


def _random_email(first: str, last: str) -> str:
    """Generate a plausible random email."""
    domains = ["example.com", "test.io", "hackathon.dev", "demo.org"]
    return f"{first.lower()}.{last.lower()}{random.randint(1, 999)}@{random.choice(domains)}"


async def run_simulator(
    shopify_client: ShopifyClient,
    session_factory: async_sessionmaker,
) -> None:
    """
    Main simulator loop. Runs continuously until cancelled.

    Creates orders every SIMULATOR_INTERVAL_MIN to SIMULATOR_INTERVAL_MAX seconds.
    """
    settings = get_settings()
    events = EventManager.get()
    logger.info("Order simulator started (interval: %d-%ds)",
                settings.SIMULATOR_INTERVAL_MIN, settings.SIMULATOR_INTERVAL_MAX)

    while True:
        try:
            # Sleep first, then create order
            delay = random.randint(
                settings.SIMULATOR_INTERVAL_MIN,
                settings.SIMULATOR_INTERVAL_MAX,
            )
            await asyncio.sleep(delay)

            # Pick 1-3 random products from local DB
            async with session_factory() as db:
                result = await db.execute(
                    select(Product)
                    .order_by(func.random())
                    .limit(random.randint(1, 3))
                )
                products = result.scalars().all()

                if not products:
                    logger.warning("No products in DB — skipping simulation")
                    continue

                # Build line items from product variants
                line_items = []
                for product in products:
                    variants = product.variants or []
                    if not variants:
                        continue
                    variant = random.choice(variants)
                    variant_gid = variant.get("id", "")
                    # Extract numeric ID from GID
                    variant_id = variant_gid.split("/")[-1] if "/" in variant_gid else variant_gid
                    line_items.append({
                        "variant_id": variant_id,
                        "quantity": random.randint(1, 3),
                    })

                if not line_items:
                    continue

                # Random customer
                first = random.choice(FIRST_NAMES)
                last = random.choice(LAST_NAMES)
                customer = {
                    "first_name": first,
                    "last_name": last,
                    "email": _random_email(first, last),
                }

                # ~15% chance: add a discount code
                discount_code = random.choice(DISCOUNT_CODES) if random.random() < 0.15 else None

                # Create order on Shopify
                result_json = await shopify_client.create_order(
                    line_items=line_items,
                    customer=customer,
                    discount_code=discount_code,
                )

                order = result_json.get("order", {})
                order_id = order.get("id")

                if order_id:
                    logger.info(
                        "Created simulated order #%s ($%s)",
                        order.get("order_number", "?"),
                        order.get("total_price", "0"),
                    )

                    # Sync the new order into local DB
                    now = datetime.now(timezone.utc).isoformat()
                    line_items_json = []
                    for li in order.get("line_items", []):
                        line_items_json.append({
                            "id": str(li.get("id", "")),
                            "title": li.get("title", ""),
                            "quantity": li.get("quantity", 0),
                            "amount": float(li.get("price", 0)) * li.get("quantity", 1),
                            "variant_id": str(li.get("variant_id", "")),
                            "product_id": str(li.get("product_id", "")),
                        })

                    new_order = Order(
                        id=f"gid://shopify/Order/{order_id}",
                        order_number=f"#{order.get('order_number', '')}",
                        total_price=float(order.get("total_price", 0)),
                        subtotal_price=float(order.get("subtotal_price", 0)),
                        total_discounts=float(order.get("total_discounts", 0)),
                        total_tax=float(order.get("total_tax", 0)),
                        currency=order.get("currency", "USD"),
                        financial_status=order.get("financial_status", "paid"),
                        fulfillment_status=order.get("fulfillment_status"),
                        line_items=line_items_json,
                        customer_id=str(order.get("customer", {}).get("id", "")) if order.get("customer") else None,
                        customer_email=order.get("customer", {}).get("email") if order.get("customer") else None,
                        customer_name=f"{first} {last}",
                        discount_codes=order.get("discount_codes", []),
                        landing_site=None,
                        referring_site=None,
                        processed_at=order.get("processed_at", now),
                        created_at=now,
                        is_simulated=True,
                    )
                    db.add(new_order)
                    await db.commit()

                    # Publish event
                    await events.publish("order.simulated", {
                        "order_id": str(order_id),
                        "order_number": order.get("order_number"),
                        "total_price": order.get("total_price", "0"),
                        "customer_name": f"{first} {last}",
                        "items": len(line_items),
                    })

                    # ~5% chance: schedule a refund after 5 min
                    if random.random() < 0.05:
                        asyncio.create_task(
                            _delayed_refund(db, order_id, session_factory, events)
                        )

        except asyncio.CancelledError:
            logger.info("Order simulator stopped")
            return
        except Exception as exc:
            logger.error("Simulator error: %s", exc, exc_info=True)
            await asyncio.sleep(10)  # Back off on errors


async def _delayed_refund(
    db_unused,
    order_id: int,
    session_factory: async_sessionmaker,
    events: EventManager,
) -> None:
    """Wait 5 minutes then mark the order as refunded in local DB."""
    try:
        await asyncio.sleep(300)  # 5 minutes
        async with session_factory() as db:
            gid = f"gid://shopify/Order/{order_id}"
            result = await db.execute(
                select(Order).where(Order.id == gid)
            )
            order = result.scalar_one_or_none()
            if order:
                order.financial_status = "refunded"
                await db.commit()
                logger.info("Marked order %s as refunded", order_id)
                await events.publish("order.refunded", {
                    "order_id": str(order_id),
                    "order_number": order.order_number,
                })
    except Exception as exc:
        logger.warning("Failed to process delayed refund for %s: %s", order_id, exc)
