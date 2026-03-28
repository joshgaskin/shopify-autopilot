"""
Seed realistic mock data so agents have rich scenarios to work with.
Designed to trigger every agent behavior: stockouts, slow movers, health issues, reorders.
"""
import random
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Product, Order, Customer

# Fixed seed for reproducible data
random.seed(42)

# ── Products ─────────────────────────────────────────────────────────────────
# Mix of: hot sellers (low stock, high velocity), steady performers,
# slow movers (declining), dead stock, and problematic listings

SAMPLE_PRODUCTS = [
    # HOT — selling fast, running low (Rick: stockout alerts, Hank: reorder)
    {"title": "Classic Black Hoodie", "handle": "classic-black-hoodie", "price": 89.00, "stock": 3, "status": "active", "image": "https://picsum.photos/seed/hoodie/400/400", "velocity_weight": 5.0},
    {"title": "Fleece Quarter-Zip", "handle": "fleece-quarter-zip", "price": 95.00, "stock": 2, "status": "active", "image": "https://picsum.photos/seed/quartzip/400/400", "velocity_weight": 4.5},
    {"title": "Vintage Wash Denim", "handle": "vintage-wash-denim", "price": 120.00, "stock": 5, "status": "active", "image": "https://picsum.photos/seed/denim/400/400", "velocity_weight": 3.8},

    # STRONG — healthy sales, good stock (Hank: Core/Strong tier)
    {"title": "Oversized White Tee", "handle": "oversized-white-tee", "price": 45.00, "stock": 52, "status": "active", "image": "https://picsum.photos/seed/whitetee/400/400", "velocity_weight": 3.0},
    {"title": "Cargo Track Pants", "handle": "cargo-track-pants", "price": 75.00, "stock": 34, "status": "active", "image": "https://picsum.photos/seed/cargo/400/400", "velocity_weight": 2.5},
    {"title": "Essential Crew Socks 3-Pack", "handle": "essential-crew-socks", "price": 22.00, "stock": 120, "status": "active", "image": "https://picsum.photos/seed/socks/400/400", "velocity_weight": 4.0},
    {"title": "Logo Snapback Cap", "handle": "logo-snapback-cap", "price": 35.00, "stock": 67, "status": "active", "image": "https://picsum.photos/seed/snapback/400/400", "velocity_weight": 2.0},
    {"title": "Heavyweight Graphic Tee", "handle": "heavyweight-graphic-tee", "price": 55.00, "stock": 28, "status": "active", "image": "https://picsum.photos/seed/graphictee/400/400", "velocity_weight": 2.2},

    # SLOW MOVERS — declining sales, excess stock (Ron: discount candidates)
    {"title": "Pastel Tie-Dye Crewneck", "handle": "pastel-tie-dye-crewneck", "price": 68.00, "stock": 45, "status": "active", "image": "https://picsum.photos/seed/tiedye/400/400", "velocity_weight": 0.3, "declining": True},
    {"title": "Linen Resort Shirt", "handle": "linen-resort-shirt", "price": 72.00, "stock": 38, "status": "active", "image": "https://picsum.photos/seed/linen/400/400", "velocity_weight": 0.2, "declining": True},
    {"title": "Neon Running Shorts", "handle": "neon-running-shorts", "price": 42.00, "stock": 55, "status": "active", "image": "https://picsum.photos/seed/neon/400/400", "velocity_weight": 0.1, "declining": True},
    {"title": "Festival Bucket Hat", "handle": "festival-bucket-hat", "price": 28.00, "stock": 72, "status": "active", "image": "https://picsum.photos/seed/bucket/400/400", "velocity_weight": 0.15, "declining": True},

    # PROBLEM LISTINGS — (Rick: health issues)
    {"title": "Colour Block Windbreaker", "handle": "colour-block-windbreaker", "price": 110.00, "stock": 0, "status": "active", "image": "https://picsum.photos/seed/windbreaker/400/400", "velocity_weight": 1.0},  # active + zero stock
    {"title": "Relaxed Linen Shirt", "handle": "relaxed-linen-shirt", "price": 65.00, "stock": 31, "status": "active", "image": None, "velocity_weight": 1.5},  # missing image
    {"title": "Nylon Crossbody Bag", "handle": "nylon-crossbody-bag", "price": 48.00, "stock": 19, "status": "active", "image": None, "velocity_weight": 0.8},  # missing image
    {"title": "Mystery Sample Tee", "handle": "mystery-sample-tee", "price": 0.00, "stock": 5, "status": "active", "image": None, "velocity_weight": 0.0},  # $0 price!

    # DRAFT — (Rick: draft with stock)
    {"title": "Corduroy Overshirt", "handle": "corduroy-overshirt", "price": 85.00, "stock": 41, "status": "draft", "image": "https://picsum.photos/seed/corduroy/400/400", "velocity_weight": 0.0},
    {"title": "Sherpa Lined Jacket", "handle": "sherpa-lined-jacket", "price": 145.00, "stock": 22, "status": "draft", "image": "https://picsum.photos/seed/sherpa/400/400", "velocity_weight": 0.0},

    # MORE ACTIVE — fill out the catalog
    {"title": "Slim Chino Pant", "handle": "slim-chino-pant", "price": 68.00, "stock": 40, "status": "active", "image": "https://picsum.photos/seed/chino/400/400", "velocity_weight": 1.8},
    {"title": "Ribbed Tank Top", "handle": "ribbed-tank-top", "price": 32.00, "stock": 60, "status": "active", "image": "https://picsum.photos/seed/tank/400/400", "velocity_weight": 1.5},
    {"title": "Wool Blend Beanie", "handle": "wool-blend-beanie", "price": 30.00, "stock": 85, "status": "active", "image": "https://picsum.photos/seed/beanie/400/400", "velocity_weight": 1.2},
    {"title": "Zip-Up Bomber Jacket", "handle": "zip-up-bomber-jacket", "price": 130.00, "stock": 11, "status": "active", "image": "https://picsum.photos/seed/bomber/400/400", "velocity_weight": 2.8},
    {"title": "French Terry Joggers", "handle": "french-terry-joggers", "price": 62.00, "stock": 25, "status": "active", "image": "https://picsum.photos/seed/joggers/400/400", "velocity_weight": 3.2},
    {"title": "Pique Polo Shirt", "handle": "pique-polo-shirt", "price": 50.00, "stock": 33, "status": "active", "image": "https://picsum.photos/seed/polo/400/400", "velocity_weight": 1.0},
    {"title": "Canvas Tote Bag", "handle": "canvas-tote-bag", "price": 25.00, "stock": 90, "status": "active", "image": "https://picsum.photos/seed/tote/400/400", "velocity_weight": 0.7},
]

# ── Customers ────────────────────────────────────────────────────────────────

FIRST_NAMES = ["Emma", "Liam", "Olivia", "Noah", "Ava", "James", "Sophia", "Mason", "Isabella", "Lucas",
               "Mia", "Ethan", "Charlotte", "Aiden", "Harper", "Jackson", "Ella", "Sebastian", "Grace", "Mateo",
               "Chloe", "Owen", "Zoe", "Leo", "Lily", "Jack", "Aria", "Henry", "Scarlett", "Wyatt"]
LAST_NAMES = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez",
              "Wilson", "Anderson", "Taylor", "Thomas", "Jackson", "White", "Harris", "Martin", "Thompson", "Moore"]
DOMAINS = ["gmail.com", "outlook.com", "yahoo.com", "icloud.com", "hotmail.com"]


async def seed_if_empty(db: AsyncSession) -> bool:
    """Seed rich mock data if the database is empty. Returns True if seeded."""
    result = await db.execute(select(func.count()).select_from(Product))
    if (result.scalar() or 0) > 0:
        return False

    now = datetime.now(timezone.utc)

    # ── Products ──
    for i, p in enumerate(SAMPLE_PRODUCTS):
        sizes = ["S", "M", "L", "XL"]
        total_stock = p["stock"]
        # Distribute stock unevenly (M and L get more)
        weights = [0.15, 0.30, 0.35, 0.20]
        variants = []
        remaining = total_stock
        for j, (size, w) in enumerate(zip(sizes, weights)):
            qty = round(total_stock * w) if j < 3 else remaining
            remaining -= qty
            if remaining < 0:
                qty += remaining
                remaining = 0
            variants.append({
                "id": f"var-{i}-{j}",
                "title": size,
                "price": p["price"],
                "sku": f"{p['handle']}-{size.lower()}",
                "inventory_quantity": max(0, qty),
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
            featured_image_url=p.get("image"),
            inventory_total=total_stock,
            created_at=(now - timedelta(days=random.randint(30, 120))).isoformat(),
            updated_at=now.isoformat(),
        ))

    # ── Customers ──
    customers = []
    for i in range(40):
        first = random.choice(FIRST_NAMES)
        last = random.choice(LAST_NAMES)
        email = f"{first.lower()}.{last.lower()}{random.randint(1,99)}@{random.choice(DOMAINS)}"
        created = now - timedelta(days=random.randint(7, 180))
        customers.append({
            "id": f"cust-{i}",
            "first_name": first,
            "last_name": last,
            "email": email,
            "created_at": created.isoformat(),
        })
        db.add(Customer(
            id=f"cust-{i}",
            email=email,
            first_name=first,
            last_name=last,
            orders_count=0,
            total_spent=0.0,
            tags=[],
            created_at=created.isoformat(),
            last_order_at=None,
        ))

    # ── Orders (last 21 days) ──
    # Create realistic ordering patterns:
    # - Hot products get ordered frequently in recent 7 days
    # - Slow movers had orders 8-14 days ago but not recently (declining)
    # - Some refunds mixed in
    active_products = [p for p in SAMPLE_PRODUCTS if p["status"] == "active" and p["stock"] > 0]
    order_num = 1000
    all_orders = []

    for day_offset in range(21, 0, -1):
        order_date = now - timedelta(days=day_offset)

        # Weekday gets more orders than weekend
        is_weekend = order_date.weekday() >= 5
        base_orders = random.randint(3, 6) if not is_weekend else random.randint(1, 3)

        # Recent days get more orders (growing store)
        if day_offset <= 7:
            base_orders = int(base_orders * 1.5)

        for _ in range(base_orders):
            order_num += 1
            customer = random.choice(customers)

            # Pick products weighted by velocity
            weights = [p.get("velocity_weight", 1.0) for p in active_products]

            # For declining products: only sell them in older period (8-21 days ago)
            if day_offset <= 7:
                weights = [
                    w if not p.get("declining") else w * 0.05
                    for w, p in zip(weights, active_products)
                ]

            total_weight = sum(weights)
            if total_weight == 0:
                continue
            normalized = [w / total_weight for w in weights]

            num_items = random.choices([1, 2, 3], weights=[0.5, 0.35, 0.15])[0]
            chosen_indices = set()
            for _ in range(num_items):
                idx = random.choices(range(len(active_products)), weights=normalized)[0]
                chosen_indices.add(idx)

            line_items = []
            total = 0.0
            for idx in chosen_indices:
                item = active_products[idx]
                qty = random.choices([1, 2, 3], weights=[0.6, 0.3, 0.1])[0]
                line_items.append({
                    "title": item["title"],
                    "variant_title": random.choices(["S", "M", "L", "XL"], weights=[0.15, 0.30, 0.35, 0.20])[0],
                    "quantity": qty,
                    "price": item["price"],
                })
                total += item["price"] * qty

            # Occasional discount code
            discount = 0.0
            discount_codes = []
            if random.random() < 0.1:
                pct = random.choice([10, 15, 20])
                discount = round(total * pct / 100, 2)
                discount_codes = [f"SAVE{pct}"]

            # Occasional refund (5% chance, mostly older orders)
            is_refund = random.random() < 0.05 and day_offset > 5
            hour = random.choices(
                range(24),
                weights=[1,1,1,1,1,1,2,3,4,5,6,7,8,8,7,6,5,6,7,8,9,8,5,2]
            )[0]

            order_id = f"order-{order_num}"
            db.add(Order(
                id=order_id,
                order_number=str(order_num),
                total_price=round(total - discount, 2),
                subtotal_price=round(total, 2),
                total_discounts=discount,
                total_tax=round((total - discount) * 0.1, 2),
                currency="USD",
                financial_status="refunded" if is_refund else "paid",
                fulfillment_status="fulfilled" if day_offset > 2 and not is_refund else None,
                line_items=line_items,
                customer_id=customer["id"],
                customer_email=customer["email"],
                customer_name=f"{customer['first_name']} {customer['last_name']}",
                discount_codes=discount_codes,
                landing_site=random.choice(["/", "/collections/all", "/products/classic-black-hoodie", None]),
                referring_site=random.choice(["https://google.com", "https://instagram.com", "direct", None]),
                processed_at=(order_date + timedelta(hours=hour, minutes=random.randint(0, 59))).isoformat(),
                created_at=order_date.isoformat(),
                is_simulated=True,
            ))
            all_orders.append({"customer_id": customer["id"], "total": total - discount})

    # ── Update customer aggregates ──
    customer_stats: dict[str, dict] = {}
    for o in all_orders:
        cid = o["customer_id"]
        stats = customer_stats.setdefault(cid, {"count": 0, "spent": 0.0})
        stats["count"] += 1
        stats["spent"] += o["total"]

    for cust in customers:
        stats = customer_stats.get(cust["id"], {"count": 0, "spent": 0.0})
        result = await db.execute(select(Customer).where(Customer.id == cust["id"]))
        c = result.scalar_one_or_none()
        if c:
            c.orders_count = stats["count"]
            c.total_spent = round(stats["spent"], 2)
            if stats["count"] > 0:
                c.last_order_at = now.isoformat()

    await db.commit()
    return True
