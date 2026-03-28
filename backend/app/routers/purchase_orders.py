"""Purchase Order API — view and manage POs created by Hank."""
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.agents.models import PurchaseOrder, POLineItem

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/purchase-orders", tags=["purchase-orders"])


@router.get("")
async def list_purchase_orders(
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """List all purchase orders with their line items."""
    query = select(PurchaseOrder).order_by(desc(PurchaseOrder.id))
    if status:
        query = query.where(PurchaseOrder.status == status)

    result = await db.execute(query)
    pos = result.scalars().all()

    output = []
    for po in pos:
        items_result = await db.execute(
            select(POLineItem).where(POLineItem.po_id == po.id)
        )
        items = items_result.scalars().all()

        output.append({
            "id": po.id,
            "poNumber": po.po_number,
            "status": po.status,
            "totalQty": po.total_qty,
            "totalCost": po.total_cost,
            "notes": po.notes,
            "createdBy": po.created_by,
            "createdAt": po.created_at,
            "updatedAt": po.updated_at,
            "lineItems": [
                {
                    "id": item.id,
                    "productId": item.product_id,
                    "productTitle": item.product_title,
                    "qty": item.qty,
                    "costPerUnit": item.cost_per_unit,
                    "totalCost": item.total_cost,
                }
                for item in items
            ],
        })

    return output


@router.get("/inbound")
async def get_inbound_stock(db: AsyncSession = Depends(get_db)):
    """Get inbound stock from active POs (draft, ordered, shipped) grouped by product."""
    active_statuses = ["draft", "ordered", "shipped"]
    result = await db.execute(
        select(PurchaseOrder).where(PurchaseOrder.status.in_(active_statuses))
    )
    active_pos = result.scalars().all()

    inbound: dict[str, dict] = {}
    for po in active_pos:
        items_result = await db.execute(
            select(POLineItem).where(POLineItem.po_id == po.id)
        )
        for item in items_result.scalars().all():
            if item.product_id not in inbound:
                inbound[item.product_id] = {
                    "productId": item.product_id,
                    "productTitle": item.product_title,
                    "inboundQty": 0,
                    "poNumbers": [],
                }
            inbound[item.product_id]["inboundQty"] += item.qty
            if po.po_number not in inbound[item.product_id]["poNumbers"]:
                inbound[item.product_id]["poNumbers"].append(po.po_number)

    return list(inbound.values())


class UpdateStatusRequest(BaseModel):
    status: str


@router.patch("/{po_id}")
async def update_po_status(
    po_id: int,
    body: UpdateStatusRequest,
    db: AsyncSession = Depends(get_db),
):
    """Update a PO's status (draft → ordered → shipped → received)."""
    result = await db.execute(select(PurchaseOrder).where(PurchaseOrder.id == po_id))
    po = result.scalar_one_or_none()
    if not po:
        return {"error": "PO not found"}

    po.status = body.status
    po.updated_at = datetime.now(timezone.utc).isoformat()
    await db.commit()

    return {"id": po.id, "poNumber": po.po_number, "status": po.status}
