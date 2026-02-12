"""
Saved events endpoints for listing, saving, and removing saved events.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.services.event_service import EventService
from app.schemas.events import (
    EventResponse,
    SaveEventResponse,
)


router = APIRouter(prefix="/api/v1/users/saved-events", tags=["Saved Events"])

event_service = EventService()


@router.get(
    "/",
    response_model=list[EventResponse],
    status_code=status.HTTP_200_OK,
    summary="List saved events",
    description="Get all saved events for the authenticated user, ordered by most recently saved.",
)
async def list_saved_events(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[EventResponse]:
    """
    List all saved events for the current user.

    Requires authentication. Returns events ordered by interested_at DESC.
    """
    return await event_service.get_saved_events(
        db=db,
        user_id=current_user.id,
    )


@router.post(
    "/{event_id}",
    response_model=SaveEventResponse,
    status_code=status.HTTP_200_OK,
    summary="Save an event",
    description="Save an event to the authenticated user's list. Idempotent.",
)
async def save_event(
    event_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SaveEventResponse:
    """
    Save an event for the current user.

    Requires authentication. Idempotent: saving an already-saved event returns success.
    """
    return await event_service.save_event(
        db=db,
        user_id=current_user.id,
        event_id=event_id,
    )


@router.delete(
    "/{event_id}",
    response_model=SaveEventResponse,
    status_code=status.HTTP_200_OK,
    summary="Remove a saved event",
    description="Remove a saved event from the authenticated user's list.",
)
async def unsave_event(
    event_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SaveEventResponse:
    """
    Remove a saved event for the current user.

    Requires authentication. Returns 404 if the event was not saved.
    """
    return await event_service.unsave_event(
        db=db,
        user_id=current_user.id,
        event_id=event_id,
    )
