"""
Unit tests for saved-events endpoints (app/routers/saved_events.py).

Endpoints:
  GET    /api/v1/users/saved-events/
  POST   /api/v1/users/saved-events/{event_id}
  DELETE /api/v1/users/saved-events/{event_id}
"""

import uuid
import pytest
from unittest.mock import AsyncMock, patch
from fastapi import HTTPException, status

from app.schemas.events import (
    EventResponse,
    SaveEventResponse,
    VenueResponse,
)


def _fake_event(**overrides) -> EventResponse:
    defaults = dict(
        id=str(uuid.uuid4()),
        title="Saved Event",
        category="arts",
        startTime="2025-08-01T18:00:00",
        endTime=None,
        venue=VenueResponse(name="ArtSpace", address="22 Wing St", latitude=22.3, longitude=114.17),
        imageUrl="",
        organizer="ArtHK",
        description="Gallery opening.",
        sourceUrl="",
        price="Free",
        bookingUrl=None,
        isSaved=True,
        interestCount=3,
        status="active",
        schedule=None,
    )
    defaults.update(overrides)
    return EventResponse(**defaults)


# ---------------------------------------------------------------------------
# GET /
# ---------------------------------------------------------------------------


class TestListSavedEvents:

    @patch("app.routers.saved_events.event_service.get_saved_events", new_callable=AsyncMock)
    def test_list_returns_200(self, mock_list, client):
        mock_list.return_value = []
        resp = client.get("/api/v1/users/saved-events/")
        assert resp.status_code == 200

    @patch("app.routers.saved_events.event_service.get_saved_events", new_callable=AsyncMock)
    def test_list_returns_array(self, mock_list, client):
        mock_list.return_value = [_fake_event()]
        data = client.get("/api/v1/users/saved-events/").json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["isSaved"] is True

    def test_list_requires_auth(self, unauthed_client):
        resp = unauthed_client.get("/api/v1/users/saved-events/")
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# POST /{event_id}
# ---------------------------------------------------------------------------


class TestSaveEvent:

    @patch("app.routers.saved_events.event_service.save_event", new_callable=AsyncMock)
    def test_save_returns_200(self, mock_save, client):
        mock_save.return_value = SaveEventResponse(success=True, message="Event saved")
        eid = str(uuid.uuid4())
        resp = client.post(f"/api/v1/users/saved-events/{eid}")
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    @patch("app.routers.saved_events.event_service.save_event", new_callable=AsyncMock)
    def test_save_idempotent(self, mock_save, client):
        mock_save.return_value = SaveEventResponse(success=True, message="Event already saved")
        eid = str(uuid.uuid4())
        resp = client.post(f"/api/v1/users/saved-events/{eid}")
        assert resp.status_code == 200

    @patch("app.routers.saved_events.event_service.save_event", new_callable=AsyncMock)
    def test_save_nonexistent_event_returns_404(self, mock_save, client):
        mock_save.side_effect = HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "not_found", "message": "Event not found"},
        )
        eid = str(uuid.uuid4())
        resp = client.post(f"/api/v1/users/saved-events/{eid}")
        assert resp.status_code == 404

    def test_save_requires_auth(self, unauthed_client):
        eid = str(uuid.uuid4())
        resp = unauthed_client.post(f"/api/v1/users/saved-events/{eid}")
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# DELETE /{event_id}
# ---------------------------------------------------------------------------


class TestUnsaveEvent:

    @patch("app.routers.saved_events.event_service.unsave_event", new_callable=AsyncMock)
    def test_unsave_returns_200(self, mock_unsave, client):
        mock_unsave.return_value = SaveEventResponse(success=True, message="Event removed from saved")
        eid = str(uuid.uuid4())
        resp = client.delete(f"/api/v1/users/saved-events/{eid}")
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    @patch("app.routers.saved_events.event_service.unsave_event", new_callable=AsyncMock)
    def test_unsave_not_saved_returns_404(self, mock_unsave, client):
        mock_unsave.side_effect = HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "not_found", "message": "Saved event not found"},
        )
        eid = str(uuid.uuid4())
        resp = client.delete(f"/api/v1/users/saved-events/{eid}")
        assert resp.status_code == 404

    def test_unsave_requires_auth(self, unauthed_client):
        eid = str(uuid.uuid4())
        resp = unauthed_client.delete(f"/api/v1/users/saved-events/{eid}")
        assert resp.status_code == 401
