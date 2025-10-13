from sqlalchemy import Column, String, Integer, Text, TIMESTAMP, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from app.database import Base


class ScraperLog(Base):
    __tablename__ = "scraper_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_name = Column(String(50), nullable=False, index=True)
    status = Column(String(20), nullable=False)
    events_scraped = Column(Integer, default=0)
    events_new = Column(Integer, default=0)
    events_updated = Column(Integer, default=0)
    error_message = Column(Text)
    started_at = Column(TIMESTAMP, nullable=False, index=True)
    completed_at = Column(TIMESTAMP)
    duration_seconds = Column(Integer)

    __table_args__ = (
        CheckConstraint(status.in_(["success", "failure"]), name="valid_status"),
    )
