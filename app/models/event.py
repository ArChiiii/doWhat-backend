from sqlalchemy import (
    Column,
    String,
    Text,
    Integer,
    Boolean,
    TIMESTAMP,
    CheckConstraint,
    Numeric,
)
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.sql import func
import uuid
from app.database import Base


class Event(Base):
    __tablename__ = "events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(500), nullable=False)
    description = Column(Text)
    event_date = Column(TIMESTAMP, nullable=False, index=True)
    event_end_date = Column(TIMESTAMP)
    venue_name = Column(String(255))
    venue_address = Column(Text)
    venue_lat = Column(Numeric(9, 6))
    venue_lng = Column(Numeric(9, 6))
    category = Column(String(50), index=True)
    price_min = Column(Integer)
    price_max = Column(Integer)
    is_free = Column(Boolean, default=False, index=True)
    image_url = Column(Text)
    image_urls = Column(ARRAY(Text), nullable=True)
    source_name = Column(String(50), index=True)
    source_url = Column(Text)
    booking_url = Column(Text)
    interest_count = Column(Integer, default=0)
    status = Column(String(20), default="active", index=True)
    scraped_at = Column(TIMESTAMP, server_default=func.now())
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        CheckConstraint(
            category.in_(
                [
                    "music",
                    "arts",
                    "food",
                    "sports",
                    "nightlife",
                    "workshops",
                    "outdoor",
                    "family",
                ]
            ),
            name="valid_category",
        ),
        CheckConstraint(
            status.in_(["active", "cancelled", "expired"]), name="valid_status"
        ),
    )
