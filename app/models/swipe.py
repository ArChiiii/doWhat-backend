from sqlalchemy import (
    Column,
    String,
    ForeignKey,
    TIMESTAMP,
    CheckConstraint,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from app.database import Base


class SwipeHistory(Base):
    __tablename__ = "swipe_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    event_id = Column(
        UUID(as_uuid=True),
        ForeignKey("events.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    direction = Column(String(10), nullable=False, index=True)
    swiped_at = Column(TIMESTAMP, server_default=func.now(), index=True)
    session_id = Column(UUID(as_uuid=True))

    __table_args__ = (
        CheckConstraint(direction.in_(["left", "right"]), name="valid_direction"),
        UniqueConstraint("user_id", "event_id", name="unique_user_event_swipe"),
    )
