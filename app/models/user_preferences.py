from sqlalchemy import Column, String, ForeignKey, Boolean, TIMESTAMP, Numeric
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.sql import func
from app.database import Base


class UserPreferences(Base):
    __tablename__ = "user_preferences"

    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    categories = Column(ARRAY(String), default=[])
    location_lat = Column(Numeric(9, 6))
    location_lng = Column(Numeric(9, 6))
    location_enabled = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
