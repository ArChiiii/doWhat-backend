from sqlalchemy import Column, String, Text, Boolean, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.sql import func
import uuid
from app.database import Base


class InstagramPost(Base):
    __tablename__ = "instagram_posts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    instagram_post_id = Column(Text)
    content = Column(Text)
    source_url = Column(Text)
    scrape_date = Column(TIMESTAMP(timezone=True))
    processing_status = Column(Text)
    processing_date = Column(TIMESTAMP(timezone=True))
    error_message = Column(Text)
    duplicate_detected = Column(Boolean, default=False)
    instagram_username = Column(Text)
    hashtags = Column(ARRAY(Text))
    feature_image_url = Column(Text)
    image_urls = Column(ARRAY(Text))
    mentions = Column(ARRAY(Text))
    tagged_users = Column(ARRAY(Text))
    remarks = Column(Text)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
