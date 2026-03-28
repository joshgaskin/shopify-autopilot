"""
Agent action model — persisted to SQLite.
"""
from sqlalchemy import JSON, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class AgentAction(Base):
    __tablename__ = "agent_actions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    action_id: Mapped[str] = mapped_column(String, unique=True)  # e.g. "rick-001"
    timestamp: Mapped[str] = mapped_column(String)
    agent: Mapped[str] = mapped_column(String)  # Rick, Hank, Ron, Marcus
    action_type: Mapped[str] = mapped_column(String)  # stockout_alert, discount_created, etc.
    title: Mapped[str] = mapped_column(String)
    details: Mapped[str] = mapped_column(String, default="")
    commentary: Mapped[str] = mapped_column(String, default="")  # Claude-generated voice
    status: Mapped[str] = mapped_column(String, default="success")  # success, failed, pending
    product_id: Mapped[str | None] = mapped_column(String, nullable=True)
    cycle: Mapped[int] = mapped_column(Integer, default=0)  # which orchestration cycle
    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    po_number: Mapped[str] = mapped_column(String, unique=True)
    status: Mapped[str] = mapped_column(String, default="draft")  # draft, ordered, shipped, received
    total_qty: Mapped[int] = mapped_column(Integer, default=0)
    total_cost: Mapped[float] = mapped_column(Float, default=0.0)
    notes: Mapped[str] = mapped_column(String, default="")
    created_by: Mapped[str] = mapped_column(String, default="Hank")  # which agent created it
    created_at: Mapped[str] = mapped_column(String, default="")
    updated_at: Mapped[str] = mapped_column(String, default="")


class POLineItem(Base):
    __tablename__ = "po_line_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    po_id: Mapped[int] = mapped_column(Integer)  # FK to purchase_orders.id
    product_id: Mapped[str] = mapped_column(String)
    product_title: Mapped[str] = mapped_column(String, default="")
    qty: Mapped[int] = mapped_column(Integer, default=0)
    cost_per_unit: Mapped[float] = mapped_column(Float, default=0.0)
    total_cost: Mapped[float] = mapped_column(Float, default=0.0)


class AgentState(Base):
    __tablename__ = "agent_states"

    name: Mapped[str] = mapped_column(String, primary_key=True)  # Rick, Hank, Ron, Marcus
    status: Mapped[str] = mapped_column(String, default="idle")  # active, idle, evaluating
    last_action: Mapped[str | None] = mapped_column(String, nullable=True)
    action_count: Mapped[int] = mapped_column(Integer, default=0)
    last_cycle_at: Mapped[str | None] = mapped_column(String, nullable=True)
