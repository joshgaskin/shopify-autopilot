"""Customer endpoints."""
import math

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Customer

router = APIRouter(tags=["customers"])


@router.get("/customers")
async def list_customers(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=250),
    search: str = Query("", description="Search by email or name"),
    db: AsyncSession = Depends(get_db),
):
    """List customers with pagination and search."""
    query = select(Customer)
    count_query = select(func.count()).select_from(Customer)

    if search:
        search_filter = (
            Customer.email.ilike(f"%{search}%")
            | Customer.first_name.ilike(f"%{search}%")
            | Customer.last_name.ilike(f"%{search}%")
        )
        query = query.where(search_filter)
        count_query = count_query.where(search_filter)

    total = (await db.execute(count_query)).scalar() or 0
    pages = math.ceil(total / limit) if total > 0 else 1
    offset = (page - 1) * limit

    result = await db.execute(
        query.order_by(Customer.created_at.desc()).offset(offset).limit(limit)
    )
    customers = result.scalars().all()

    return {
        "data": [_customer_to_dict(c) for c in customers],
        "total": total,
        "page": page,
        "limit": limit,
        "pages": pages,
    }


@router.get("/customers/{customer_id:path}")
async def get_customer(
    customer_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a single customer by ID (Shopify GID)."""
    result = await db.execute(select(Customer).where(Customer.id == customer_id))
    customer = result.scalar_one_or_none()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return _customer_to_dict(customer)


def _customer_to_dict(c: Customer) -> dict:
    return {
        "id": c.id,
        "email": c.email,
        "first_name": c.first_name,
        "last_name": c.last_name,
        "orders_count": c.orders_count,
        "total_spent": c.total_spent,
        "tags": c.tags or [],
        "created_at": c.created_at,
        "last_order_at": c.last_order_at,
    }
