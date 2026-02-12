"""
Event endpoints for feed generation, map display, detail view, and swipe recording.
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, get_current_user_optional
from app.models.user import User
from app.services.event_service import EventService
from app.schemas.events import (
    EventResponse,
    EventFeedResponse,
    MapEventsResponse,
    SwipeRequest,
    SwipeActionResponse,
)


router = APIRouter(prefix="/api/v1/events", tags=["Events"])

event_service = EventService()


@router.get(
    "/feed",
    response_model=EventFeedResponse,
    status_code=status.HTTP_200_OK,
    summary="Get event feed",
    description="Get paginated feed of active, upcoming events. Supports category and time filtering.",
)
async def get_event_feed(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=100, description="Events per page"),
    categories: Optional[str] = Query(None, description="Comma-separated category filter"),
    time_filter: Optional[str] = Query(None, description="Time filter: today, week, all"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
) -> EventFeedResponse:
    """
    Get paginated event feed.

    Supports optional authentication to mark saved events.
    Filter by categories (comma-separated) and time window.
    """
    user_id = current_user.id if current_user else None
    return await event_service.get_event_feed(
        db=db,
        user_id=user_id,
        page=page,
        limit=limit,
        categories=categories,
        time_filter=time_filter,
    )


@router.get(
    "/map",
    response_model=MapEventsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get map events",
    description="Get events for map display with optional location radius filtering.",
)
async def get_map_events(
    lat: Optional[float] = Query(None, description="Center latitude"),
    lng: Optional[float] = Query(None, description="Center longitude"),
    radius: int = Query(50000, description="Radius in meters"),
    time_filter: Optional[str] = Query(None, description="Time filter: today, week, all"),
    categories: Optional[str] = Query(None, description="Comma-separated category filter"),
    limit: int = Query(200, ge=1, le=500, description="Maximum events to return"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
) -> MapEventsResponse:
    """
    Get events for map display.

    Supports optional authentication to mark saved events.
    Filter by location radius, categories, and time window.
    """
    user_id = current_user.id if current_user else None
    return await event_service.get_map_events(
        db=db,
        user_id=user_id,
        lat=lat,
        lng=lng,
        radius_m=radius,
        time_filter=time_filter,
        categories=categories,
        limit=limit,
    )


@router.get(
    "/{event_id}",
    response_model=EventResponse,
    status_code=status.HTTP_200_OK,
    summary="Get event details",
    description="Get full details for a single event by ID.",
)
async def get_event_detail(
    event_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
) -> EventResponse:
    """
    Get a single event by ID.

    Supports optional authentication to indicate if the event is saved.
    """
    user_id = current_user.id if current_user else None
    return await event_service.get_event_by_id(
        db=db,
        event_id=event_id,
        user_id=user_id,
    )


@router.post(
    "/{event_id}/swipe",
    response_model=SwipeActionResponse,
    status_code=status.HTTP_200_OK,
    summary="Record swipe action",
    description="Record a left or right swipe on an event. Requires authentication.",
)
async def record_swipe(
    event_id: str,
    request: SwipeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SwipeActionResponse:
    """
    Record a swipe action on an event.

    Requires authentication. Upserts the swipe record.
    """
    return await event_service.record_swipe(
        db=db,
        user_id=current_user.id,
        event_id=event_id,
        direction=request.direction,
    )
