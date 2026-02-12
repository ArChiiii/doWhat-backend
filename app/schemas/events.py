"""
Event schemas for request/response validation.
"""

from pydantic import BaseModel, Field
from typing import Optional


class VenueResponse(BaseModel):
    name: str = Field("", description="Venue name")
    address: str = Field("", description="Venue address")
    latitude: float = Field(0.0, description="Venue latitude")
    longitude: float = Field(0.0, description="Venue longitude")


class EventResponse(BaseModel):
    id: str
    title: str
    category: str = "other"
    startTime: str          # ISO8601 from event_date
    endTime: Optional[str] = None  # from event_end_date
    venue: VenueResponse
    imageUrl: str = ""
    organizer: str = ""     # from source_name
    description: str = ""
    sourceUrl: str = ""
    price: Optional[str] = None  # computed from price_min/max/is_free
    bookingUrl: Optional[str] = None
    isSaved: bool = False
    interestCount: int = 0
    status: str = "active"
    schedule: Optional[dict] = None

    model_config = {"from_attributes": True}


class EventFeedResponse(BaseModel):
    events: list[EventResponse]
    count: int
    total: int
    page: int = 1
    hasMore: bool = False


class MapEventsResponse(BaseModel):
    events: list[EventResponse]
    count: int
    bounds: Optional[dict] = None


class SwipeRequest(BaseModel):
    direction: str = Field(..., pattern="^(left|right)$")


class SwipeActionResponse(BaseModel):
    success: bool
    message: str


class SaveEventResponse(BaseModel):
    success: bool
    message: str
