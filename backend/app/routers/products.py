"""Product endpoints."""
import math

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Product

router = APIRouter(tags=["products"])


@router.get("/products")
async def list_products(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=250),
    search: str = Query("", description="Search by title"),
    status: str = Query("", description="Filter by status"),
    db: AsyncSession = Depends(get_db),
):
    """List products with pagination, search, and status filter."""
    query = select(Product)
    count_query = select(func.count()).select_from(Product)

    if search:
        query = query.where(Product.title.ilike(f"%{search}%"))
        count_query = count_query.where(Product.title.ilike(f"%{search}%"))

    if status:
        query = query.where(Product.status == status.lower())
        count_query = count_query.where(Product.status == status.lower())

    total = (await db.execute(count_query)).scalar() or 0
    pages = math.ceil(total / limit) if total > 0 else 1
    offset = (page - 1) * limit

    result = await db.execute(
        query.order_by(Product.updated_at.desc()).offset(offset).limit(limit)
    )
    products = result.scalars().all()

    return {
        "data": [_product_to_dict(p) for p in products],
        "total": total,
        "page": page,
        "limit": limit,
        "pages": pages,
    }


@router.get("/products/{product_id:path}")
async def get_product(
    product_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a single product by ID (Shopify GID)."""
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return _product_to_dict(product)


@router.post("/products")
async def create_product(request: Request):
    """Create a product on Shopify (passthrough)."""
    shopify = request.app.state.shopify
    body = await request.json()

    # Use REST API to create product
    result = await shopify.rest("POST", "products.json", json=body)
    return result


def _product_to_dict(p: Product) -> dict:
    return {
        "id": p.id,
        "title": p.title,
        "handle": p.handle,
        "status": p.status,
        "vendor": p.vendor,
        "product_type": p.product_type,
        "price_min": p.price_min,
        "price_max": p.price_max,
        "variants": p.variants or [],
        "collections": p.collections or [],
        "featured_image_url": p.featured_image_url,
        "inventory_total": p.inventory_total,
        "created_at": p.created_at,
        "updated_at": p.updated_at,
    }
