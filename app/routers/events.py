"""
Event endpoints for feed generation, map display, detail view, and swipe recording.
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from fastapi_pagination.cursor import CursorPage, CursorParams
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, get_current_user_optional
from app.models.user import User
from app.models.event import Event
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
    response_model=CursorPage[EventResponse],
    status_code=status.HTTP_200_OK,
    summary="Get event feed",
    description="Get cursor-paginated feed of active, upcoming events with filtering.",
)
async def get_event_feed(
    cursor: Optional[str] = Query(None, description="Pagination cursor"),
    size: int = Query(20, ge=1, le=100, alias="limit", description="Events per page"),
    categories: Optional[str] = Query(None, description="Comma-separated category filter"),
    time_filter: Optional[str] = Query(None, description="Time filter: today, week, all"),
    date_from: Optional[str] = Query(None, description="Start date ISO8601 (e.g. 2026-03-01)"),
    date_to: Optional[str] = Query(None, description="End date ISO8601 (e.g. 2026-03-31)"),
    price_min: Optional[int] = Query(None, ge=0, description="Minimum price in HKD"),
    price_max: Optional[int] = Query(None, ge=0, description="Maximum price in HKD"),
    is_free: Optional[bool] = Query(None, description="Filter free events only"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
) -> CursorPage[EventResponse]:
    """
    Get cursor-paginated event feed.

    Supports optional authentication to mark saved events.
    Filter by categories, time window, date range, and price.
    """
    # Build the query
    query = event_service.build_event_feed_query(
        db=db,
        categories=categories,
        time_filter=time_filter,
        date_from=date_from,
        date_to=date_to,
        price_min=price_min,
        price_max=price_max,
        is_free=is_free,
    )

    # Get saved event IDs for authenticated users
    user_id = current_user.id if current_user else None
    saved_ids = set()
    if user_id:
        saved_ids = event_service._get_saved_event_ids(db, user_id)

    # Create transformer that marks saved events
    def transform_items(items: list[Event]) -> list[EventResponse]:
        return [
            event_service._format_event(e, is_saved=(e.id in saved_ids))
            for e in items
        ]

    # Apply cursor pagination
    result = paginate(
        db,
        query,
        params=CursorParams(size=size, cursor=cursor),
        transformer=transform_items,
    )
    return result


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
