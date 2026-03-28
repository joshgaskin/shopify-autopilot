"""
Seed sample products + orders so agents have data to work with.
Called when Shopify sync fails and DB is empty.
"""
import uuid
import random
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Product, Order


SAMPLE_PRODUCTS = [
    {"title": "Classic Black Hoodie", "handle": "classic-black-hoodie", "price": 89.00, "stock": 4, "status": "active"},
    {"title": "Oversized White Tee", "handle": "oversized-white-tee", "price": 45.00, "stock": 52, "status": "active"},
    {"title": "Cargo Track Pants", "handle": "cargo-track-pants", "price": 75.00, "stock": 18, "status": "active"},
    {"title": "Vintage Wash Denim", "handle": "vintage-wash-denim", "price": 120.00, "stock": 8, "status": "active"},
    {"title": "Logo Snapback Cap", "handle": "logo-snapback-cap", "price": 35.00, "stock": 67, "status": "active"},
    {"title": "Fleece Quarter-Zip", "handle": "fleece-quarter-zip", "price": 95.00, "stock": 2, "status": "active"},
    {"title": "Relaxed Linen Shirt", "handle": "relaxed-linen-shirt", "price": 65.00, "stock": 31, "status": "active"},
    {"title": "Colour Block Windbreaker", "handle": "colour-block-windbreaker", "price": 110.00, "stock": 0, "status": "active"},
    {"title": "Essential Crew Socks 3-Pack", "handle": "essential-crew-socks", "price": 22.00, "stock": 120, "status": "active"},
    {"title": "Heavyweight Graphic Tee", "handle": "heavyweight-graphic-tee", "price": 55.00, "stock": 15, "status": "active"},
    {"title": "Corduroy Overshirt", "handle": "corduroy-overshirt", "price": 85.00, "stock": 41, "status": "draft"},
    {"title": "Nylon Crossbody Bag", "handle": "nylon-crossbody-bag", "price": 48.00, "stock": 9, "status": "active"},
]


async def seed_if_empty(db: AsyncSession) -> bool:
    """Seed sample data if the database is empty. Returns True if seeded."""
    result = await db.execute(select(func.count()).select_from(Product))
    if (result.scalar() or 0) > 0:
        return False

    now = datetime.now(timezone.utc)

    # Create products
    for i, p in enumerate(SAMPLE_PRODUCTS):
        sizes = ["S", "M", "L", "XL"]
        per_size = max(0, p["stock"] // len(sizes))
        remainder = max(0, p["stock"] % len(sizes))
        variants = []
        for j, size in enumerate(sizes):
            qty = per_size + (1 if j == 0 and remainder > 0 else 0)
            variants.append({
                "id": f"var-{i}-{j}",
                "title": size,
                "price": p["price"],
                "sku": f"{p['handle']}-{size.lower()}",
                "inventory_quantity": qty,
            })

        db.add(Product(
            id=f"prod-{i}",
            title=p["title"],
            handle=p["handle"],
            status=p["status"],
            vendor="Plus2",
            product_type="Apparel",
            price_min=p["price"],
            price_max=p["price"],
            variants=variants,
            collections=["All"],
            featured_image_url=None,
            inventory_total=p["stock"],
            created_at=(now - timedelta(days=random.randint(30, 90))).isoformat(),
            updated_at=now.isoformat(),
        ))

    # Create orders (last 14 days, varying velocity)
    products_for_orders = [p for p in SAMPLE_PRODUCTS if p["status"] == "active" and p["stock"] > 0]
    order_num = 1000

    for day_offset in range(14, 0, -1):
        order_date = now - timedelta(days=day_offset)
        # More orders on recent days (simulate growing store)
        num_orders = random.randint(2, 5) if day_offset <= 7 else random.randint(1, 3)

        for _ in range(num_orders):
            order_num += 1
            # Pick 1-3 products
            items = random.sample(products_for_orders, min(random.randint(1, 3), len(products_for_orders)))
            line_items = []
            total = 0.0
            for item in items:
                qty = random.randint(1, 2)
                line_items.append({
                    "title": item["title"],
                    "variant_title": random.choice(["S", "M", "L", "XL"]),
                    "quantity": qty,
                    "price": item["price"],
                })
                total += item["price"] * qty

            db.add(Order(
                id=f"order-{order_num}",
                order_number=str(order_num),
                total_price=round(total, 2),
                subtotal_price=round(total, 2),
                total_discounts=0,
                total_tax=round(total * 0.1, 2),
                currency="USD",
                financial_status="paid",
                fulfillment_status="fulfilled" if day_offset > 2 else None,
                line_items=line_items,
                customer_id=f"cust-{random.randint(1, 20)}",
                customer_email=f"customer{random.randint(1, 20)}@example.com",
                customer_name=f"Customer {random.randint(1, 20)}",
                discount_codes=[],
                processed_at=(order_date + timedelta(hours=random.randint(9, 22))).isoformat(),
                created_at=order_date.isoformat(),
                is_simulated=True,
            ))

    await db.commit()
    return True
