"""Store info endpoint."""
from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.models import Product, Order, Customer

router = APIRouter(tags=["store"])


@router.get("/store")
async def get_store(db: AsyncSession = Depends(get_db)):
    """Get store overview with counts."""
    settings = get_settings()

    product_count = (await db.execute(
        select(func.count()).select_from(Product)
    )).scalar() or 0

    order_count = (await db.execute(
        select(func.count()).select_from(Order)
    )).scalar() or 0

    customer_count = (await db.execute(
        select(func.count()).select_from(Customer)
    )).scalar() or 0

    # Get latest order timestamp as proxy for last_sync
    last_order = (await db.execute(
        select(Order.created_at).order_by(Order.created_at.desc()).limit(1)
    )).scalar()

    return {
        "domain": settings.SHOPIFY_STORE_URL,
        "name": settings.SHOPIFY_STORE_URL.split(".")[0],
        "currency": "USD",
        "product_count": product_count,
        "order_count": order_count,
        "customer_count": customer_count,
        "last_sync": last_order,
    }
