"""
Event service for feed generation, swipe recording, and saved events management.
"""

from typing import Optional
from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from fastapi import HTTPException, status

from app.models.event import Event
from app.models.interested_event import InterestedEvent
from app.models.swipe import SwipeHistory
from app.schemas.events import (
    EventResponse,
    EventFeedResponse,
    MapEventsResponse,
    SwipeActionResponse,
    SaveEventResponse,
    VenueResponse,
)


class EventService:
    """
    Service handling event feed generation, swipe recording,
    and saved events management.
    """

    # ========================================================================
    # Event Formatting
    # ========================================================================

    @staticmethod
    def _format_price(event: Event) -> Optional[str]:
        """
        Compute display price string from event pricing fields.

        Args:
            event: Event database row

        Returns:
            Formatted price string or None
        """
        if event.is_free:
            return "Free"
        if event.price_min is not None and event.price_max is not None:
            if event.price_min == event.price_max:
                return f"HK${event.price_min}"
            return f"HK${event.price_min} - HK${event.price_max}"
        if event.price_min is not None:
            return f"HK${event.price_min}+"
        return None

    @staticmethod
    def _format_event(event: Event, is_saved: bool = False) -> EventResponse:
        """
        Convert a database Event row to an EventResponse schema.

        Args:
            event: Event database row
            is_saved: Whether the current user has saved this event

        Returns:
            EventResponse schema instance
        """
        return EventResponse(
            id=str(event.id),
            title=event.title,
            category=event.category or "other",
            startTime=event.event_date.isoformat() if event.event_date else "",
            endTime=event.event_end_date.isoformat() if event.event_end_date else None,
            venue=VenueResponse(
                name=event.venue_name or "",
                address=event.venue_address or "",
                latitude=float(event.venue_lat) if event.venue_lat is not None else 0.0,
                longitude=float(event.venue_lng) if event.venue_lng is not None else 0.0,
            ),
            imageUrl=event.image_url or "",
            organizer=event.source_name or "",
            description=event.description or "",
            sourceUrl=event.source_url or "",
            price=EventService._format_price(event),
            bookingUrl=event.booking_url,
            isSaved=is_saved,
            interestCount=event.interest_count or 0,
            status=event.status or "active",
            schedule=event.schedule,
        )

    # ========================================================================
    # Shared Query Helpers
    # ========================================================================

    @staticmethod
    def _active_event_filters(time_filter: Optional[str] = None) -> list:
        """
        Build a list of SQLAlchemy filter clauses for active, future/ongoing events.

        Args:
            time_filter: Optional time constraint (today, week, all)

        Returns:
            List of filter clauses
        """
        now = datetime.utcnow()
        filters = [Event.status == "active"]

        # Only future or currently-ongoing events:
        # event_end_date >= now  OR  (no end date AND event_date within last 6h)
        six_hours_ago = now - timedelta(hours=6)
        filters.append(
            or_(
                Event.event_end_date >= now,
                and_(Event.event_end_date.is_(None), Event.event_date >= six_hours_ago),
            )
        )

        if time_filter == "today":
            end_of_day = now.replace(hour=23, minute=59, second=59, microsecond=999999)
            filters.append(Event.event_date <= end_of_day)
        elif time_filter == "week":
            end_of_week = now + timedelta(days=7)
            filters.append(Event.event_date <= end_of_week)
        # "now" and "all" impose no additional upper-bound filter

        return filters

    @staticmethod
    def _get_saved_event_ids(db: Session, user_id: UUID) -> set:
        """
        Batch-fetch all saved event IDs for a user.

        Args:
            db: Database session
            user_id: User UUID

        Returns:
            Set of event ID UUIDs that the user has saved
        """
        rows = (
            db.query(InterestedEvent.event_id)
            .filter(InterestedEvent.user_id == user_id)
            .all()
        )
        return {row[0] for row in rows}

    # ========================================================================
    # Event Feed
    # ========================================================================

    async def get_event_feed(
        self,
        db: Session,
        user_id: Optional[UUID] = None,
        page: int = 1,
        limit: int = 50,
        categories: Optional[str] = None,
        time_filter: Optional[str] = None,
    ) -> EventFeedResponse:
        """
        Get paginated event feed with active, upcoming events.

        Args:
            db: Database session
            user_id: Optional authenticated user ID
            page: Page number (1-indexed)
            limit: Events per page
            categories: Comma-separated category filter
            time_filter: Time constraint (today, week, all)

        Returns:
            EventFeedResponse with paginated events
        """
        filters = self._active_event_filters(time_filter)

        if categories:
            cat_list = [c.strip() for c in categories.split(",") if c.strip()]
            if cat_list:
                filters.append(Event.category.in_(cat_list))

        # Total count
        total = db.query(Event).filter(*filters).count()

        # Paginated results
        offset = (page - 1) * limit
        events = (
            db.query(Event)
            .filter(*filters)
            .order_by(Event.event_date.asc())
            .offset(offset)
            .limit(limit)
            .all()
        )

        # Batch-fetch saved IDs
        saved_ids: set = set()
        if user_id:
            saved_ids = self._get_saved_event_ids(db, user_id)

        event_responses = [
            self._format_event(e, is_saved=(e.id in saved_ids)) for e in events
        ]

        return EventFeedResponse(
            events=event_responses,
            count=len(event_responses),
            total=total,
            page=page,
            hasMore=(offset + limit) < total,
        )

    # ========================================================================
    # Map Events
    # ========================================================================

    async def get_map_events(
        self,
        db: Session,
        user_id: Optional[UUID] = None,
        lat: Optional[float] = None,
        lng: Optional[float] = None,
        radius_m: int = 50000,
        time_filter: Optional[str] = None,
        categories: Optional[str] = None,
        limit: int = 200,
    ) -> MapEventsResponse:
        """
        Get events for map display, optionally filtered by location radius.

        Args:
            db: Database session
            user_id: Optional authenticated user ID
            lat: Center latitude
            lng: Center longitude
            radius_m: Radius in meters
            time_filter: Time constraint
            categories: Comma-separated category filter
            limit: Maximum events to return

        Returns:
            MapEventsResponse with events and computed bounds
        """
        filters = self._active_event_filters(time_filter)

        # Only events with coordinates
        filters.append(Event.venue_lat.isnot(None))
        filters.append(Event.venue_lng.isnot(None))

        if categories:
            cat_list = [c.strip() for c in categories.split(",") if c.strip()]
            if cat_list:
                filters.append(Event.category.in_(cat_list))

        # Approximate bounding box filter when center coordinates are provided
        if lat is not None and lng is not None:
            import math

            # 1 degree latitude ~ 111,320 meters
            lat_delta = radius_m / 111320.0
            # 1 degree longitude varies by latitude (cos approximation)
            cos_lat = math.cos(math.radians(float(lat)))
            lng_delta = radius_m / (111320.0 * max(cos_lat, 0.0001))

            filters.append(Event.venue_lat >= lat - lat_delta)
            filters.append(Event.venue_lat <= lat + lat_delta)
            filters.append(Event.venue_lng >= lng - lng_delta)
            filters.append(Event.venue_lng <= lng + lng_delta)

        events = (
            db.query(Event)
            .filter(*filters)
            .order_by(Event.event_date.asc())
            .limit(limit)
            .all()
        )

        # Batch-fetch saved IDs
        saved_ids: set = set()
        if user_id:
            saved_ids = self._get_saved_event_ids(db, user_id)

        event_responses = [
            self._format_event(e, is_saved=(e.id in saved_ids)) for e in events
        ]

        # Compute bounds from results
        bounds = None
        if event_responses:
            lats = [
                float(e.venue.latitude)
                for e in event_responses
                if e.venue.latitude != 0.0
            ]
            lngs = [
                float(e.venue.longitude)
                for e in event_responses
                if e.venue.longitude != 0.0
            ]
            if lats and lngs:
                bounds = {
                    "ne": {"latitude": max(lats), "longitude": max(lngs)},
                    "sw": {"latitude": min(lats), "longitude": min(lngs)},
                }

        return MapEventsResponse(
            events=event_responses,
            count=len(event_responses),
            bounds=bounds,
        )

    # ========================================================================
    # Single Event
    # ========================================================================

    async def get_event_by_id(
        self,
        db: Session,
        event_id: str,
        user_id: Optional[UUID] = None,
    ) -> EventResponse:
        """
        Get a single event by ID.

        Args:
            db: Database session
            event_id: Event UUID string
            user_id: Optional authenticated user ID

        Returns:
            EventResponse for the requested event

        Raises:
            HTTPException: 404 if event not found
        """
        event = db.query(Event).filter(Event.id == event_id).first()
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "not_found", "message": "Event not found"},
            )

        is_saved = False
        if user_id:
            saved = (
                db.query(InterestedEvent)
                .filter(
                    InterestedEvent.user_id == user_id,
                    InterestedEvent.event_id == event.id,
                )
                .first()
            )
            is_saved = saved is not None

        return self._format_event(event, is_saved=is_saved)

    # ========================================================================
    # Swipe Recording
    # ========================================================================

    async def record_swipe(
        self,
        db: Session,
        user_id: UUID,
        event_id: str,
        direction: str,
    ) -> SwipeActionResponse:
        """
        Record a swipe action (upsert into swipe_history).

        Args:
            db: Database session
            user_id: Authenticated user UUID
            event_id: Event UUID string
            direction: 'left' or 'right'

        Returns:
            SwipeActionResponse confirming the action

        Raises:
            HTTPException: 404 if event not found
        """
        # Verify event exists
        event = db.query(Event).filter(Event.id == event_id).first()
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "not_found", "message": "Event not found"},
            )

        # Upsert swipe record
        existing = (
            db.query(SwipeHistory)
            .filter(
                SwipeHistory.user_id == user_id,
                SwipeHistory.event_id == event_id,
            )
            .first()
        )

        if existing:
            existing.direction = direction
            existing.swiped_at = datetime.utcnow()
        else:
            swipe = SwipeHistory(
                user_id=user_id,
                event_id=event_id,
                direction=direction,
            )
            db.add(swipe)

        db.commit()

        return SwipeActionResponse(
            success=True,
            message=f"Swipe {direction} recorded",
        )

    # ========================================================================
    # Saved Events
    # ========================================================================

    async def save_event(
        self,
        db: Session,
        user_id: UUID,
        event_id: str,
    ) -> SaveEventResponse:
        """
        Save an event for the user (idempotent).

        Args:
            db: Database session
            user_id: Authenticated user UUID
            event_id: Event UUID string

        Returns:
            SaveEventResponse confirming the action

        Raises:
            HTTPException: 404 if event not found
        """
        # Verify event exists
        event = db.query(Event).filter(Event.id == event_id).first()
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "not_found", "message": "Event not found"},
            )

        # Check if already saved (idempotent)
        existing = (
            db.query(InterestedEvent)
            .filter(
                InterestedEvent.user_id == user_id,
                InterestedEvent.event_id == event_id,
            )
            .first()
        )

        if existing:
            return SaveEventResponse(
                success=True,
                message="Event already saved",
            )

        # Create new saved record
        interested = InterestedEvent(
            user_id=user_id,
            event_id=event_id,
        )
        db.add(interested)

        # Increment interest count
        event.interest_count = (event.interest_count or 0) + 1

        db.commit()

        return SaveEventResponse(
            success=True,
            message="Event saved",
        )

    async def unsave_event(
        self,
        db: Session,
        user_id: UUID,
        event_id: str,
    ) -> SaveEventResponse:
        """
        Remove a saved event for the user.

        Args:
            db: Database session
            user_id: Authenticated user UUID
            event_id: Event UUID string

        Returns:
            SaveEventResponse confirming the action

        Raises:
            HTTPException: 404 if event was not saved
        """
        existing = (
            db.query(InterestedEvent)
            .filter(
                InterestedEvent.user_id == user_id,
                InterestedEvent.event_id == event_id,
            )
            .first()
        )

        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "not_found", "message": "Saved event not found"},
            )

        db.delete(existing)

        # Decrement interest count
        event = db.query(Event).filter(Event.id == event_id).first()
        if event and event.interest_count and event.interest_count > 0:
            event.interest_count = event.interest_count - 1

        db.commit()

        return SaveEventResponse(
            success=True,
            message="Event removed from saved",
        )

    async def get_saved_events(
        self,
        db: Session,
        user_id: UUID,
    ) -> list[EventResponse]:
        """
        Get all saved events for a user, ordered by most recently saved.

        Args:
            db: Database session
            user_id: Authenticated user UUID

        Returns:
            List of EventResponse for saved events
        """
        saved_records = (
            db.query(InterestedEvent)
            .filter(InterestedEvent.user_id == user_id)
            .order_by(InterestedEvent.interested_at.desc())
            .all()
        )

        if not saved_records:
            return []

        event_ids = [r.event_id for r in saved_records]

        events_by_id = {}
        events = db.query(Event).filter(Event.id.in_(event_ids)).all()
        for e in events:
            events_by_id[e.id] = e

        # Preserve saved-order (interested_at DESC)
        result = []
        for record in saved_records:
            event = events_by_id.get(record.event_id)
            if event:
                result.append(self._format_event(event, is_saved=True))

        return result
