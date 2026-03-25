"""Inventory endpoint — pulls from product variants JSON in SQLite."""
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Product

router = APIRouter(tags=["inventory"])


@router.get("/inventory")
async def get_inventory(db: AsyncSession = Depends(get_db)):
    """Get inventory levels from product variants stored in SQLite."""
    result = await db.execute(select(Product))
    products = result.scalars().all()

    inventory = []
    for product in products:
        variants = product.variants or []
        for variant in variants:
            inventory.append({
                "variant_id": variant.get("id", ""),
                "product_id": product.id,
                "product_title": product.title,
                "variant_title": variant.get("title", ""),
                "sku": variant.get("sku", ""),
                "quantity": variant.get("inventory_quantity", 0),
            })

    return inventory
