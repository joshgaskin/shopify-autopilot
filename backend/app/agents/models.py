"""
Agent action model — persisted to SQLite.
"""
from sqlalchemy import JSON, Integer, String
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


class AgentState(Base):
    __tablename__ = "agent_states"

    name: Mapped[str] = mapped_column(String, primary_key=True)  # Rick, Hank, Ron, Marcus
    status: Mapped[str] = mapped_column(String, default="idle")  # active, idle, evaluating
    last_action: Mapped[str | None] = mapped_column(String, nullable=True)
    action_count: Mapped[int] = mapped_column(Integer, default=0)
    last_cycle_at: Mapped[str | None] = mapped_column(String, nullable=True)
