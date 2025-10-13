from sqlalchemy import Column, ForeignKey, TIMESTAMP, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from app.database import Base


class InterestedEvent(Base):
    __tablename__ = "interested_events"

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
    interested_at = Column(TIMESTAMP, server_default=func.now(), index=True)

    __table_args__ = (
        UniqueConstraint("user_id", "event_id", name="unique_user_event_interest"),
    )
