"""
Unit tests for event endpoints (app/routers/events.py).

Endpoints:
  GET  /api/v1/events/feed
  GET  /api/v1/events/map
  GET  /api/v1/events/{event_id}
  POST /api/v1/events/{event_id}/swipe
"""

import uuid
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.schemas.events import (
    EventResponse,
    EventFeedResponse,
    MapEventsResponse,
    SwipeActionResponse,
    VenueResponse,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fake_event(**overrides) -> EventResponse:
    defaults = dict(
        id=str(uuid.uuid4()),
        title="Test Concert",
        category="music",
        startTime="2025-07-01T20:00:00",
        endTime=None,
        venue=VenueResponse(name="Central Harbourfront", address="1 HK Ave", latitude=22.28, longitude=114.16),
        imageUrl="https://cdn.example.com/img.jpg",
        organizer="PopTicket",
        description="A great show.",
        sourceUrl="https://popticket.hk/event/1",
        price="HK$280",
        bookingUrl="https://popticket.hk/book/1",
        isSaved=False,
        interestCount=5,
        status="active",
        schedule=None,
    )
    defaults.update(overrides)
    return EventResponse(**defaults)


# ---------------------------------------------------------------------------
# GET /feed
# ---------------------------------------------------------------------------


class TestEventFeed:
    """GET /api/v1/events/feed"""

    @patch("app.routers.events.event_service.get_event_feed", new_callable=AsyncMock)
    def test_feed_returns_200(self, mock_feed, client):
        mock_feed.return_value = EventFeedResponse(
            events=[], count=0, total=0, page=1, hasMore=False,
        )
        resp = client.get("/api/v1/events/feed")
        assert resp.status_code == 200

    @patch("app.routers.events.event_service.get_event_feed", new_callable=AsyncMock)
    def test_feed_response_schema(self, mock_feed, client):
        ev = _fake_event()
        mock_feed.return_value = EventFeedResponse(
            events=[ev], count=1, total=1, page=1, hasMore=False,
        )
        data = client.get("/api/v1/events/feed").json()
        assert "events" in data
        assert "count" in data
        assert "total" in data
        assert "hasMore" in data
        assert data["count"] == 1

    @patch("app.routers.events.event_service.get_event_feed", new_callable=AsyncMock)
    def test_feed_pagination_params(self, mock_feed, client):
        mock_feed.return_value = EventFeedResponse(
            events=[], count=0, total=0, page=2, hasMore=False,
        )
        client.get("/api/v1/events/feed?page=2&limit=10")
        call_kwargs = mock_feed.call_args.kwargs
        assert call_kwargs["page"] == 2
        assert call_kwargs["limit"] == 10

    def test_feed_invalid_page_returns_422(self, client):
        resp = client.get("/api/v1/events/feed?page=0")
        assert resp.status_code == 422

    def test_feed_limit_exceeds_max_returns_422(self, client):
        resp = client.get("/api/v1/events/feed?limit=999")
        assert resp.status_code == 422

    @patch("app.routers.events.event_service.get_event_feed", new_callable=AsyncMock)
    def test_feed_with_category_filter(self, mock_feed, client):
        mock_feed.return_value = EventFeedResponse(
            events=[], count=0, total=0, page=1, hasMore=False,
        )
        client.get("/api/v1/events/feed?categories=music,arts")
        call_kwargs = mock_feed.call_args.kwargs
        assert call_kwargs["categories"] == "music,arts"

    @patch("app.routers.events.event_service.get_event_feed", new_callable=AsyncMock)
    def test_feed_with_time_filter(self, mock_feed, client):
        mock_feed.return_value = EventFeedResponse(
            events=[], count=0, total=0, page=1, hasMore=False,
        )
        client.get("/api/v1/events/feed?time_filter=today")
        call_kwargs = mock_feed.call_args.kwargs
        assert call_kwargs["time_filter"] == "today"


# ---------------------------------------------------------------------------
# GET /map
# ---------------------------------------------------------------------------


class TestMapEvents:
    """GET /api/v1/events/map"""

    @patch("app.routers.events.event_service.get_map_events", new_callable=AsyncMock)
    def test_map_returns_200(self, mock_map, client):
        mock_map.return_value = MapEventsResponse(events=[], count=0, bounds=None)
        resp = client.get("/api/v1/events/map")
        assert resp.status_code == 200

    @patch("app.routers.events.event_service.get_map_events", new_callable=AsyncMock)
    def test_map_response_schema(self, mock_map, client):
        mock_map.return_value = MapEventsResponse(events=[], count=0, bounds=None)
        data = client.get("/api/v1/events/map").json()
        assert "events" in data
        assert "count" in data

    @patch("app.routers.events.event_service.get_map_events", new_callable=AsyncMock)
    def test_map_passes_location_params(self, mock_map, client):
        mock_map.return_value = MapEventsResponse(events=[], count=0, bounds=None)
        client.get("/api/v1/events/map?lat=22.28&lng=114.16&radius=10000")
        kw = mock_map.call_args.kwargs
        assert kw["lat"] == 22.28
        assert kw["lng"] == 114.16
        assert kw["radius_m"] == 10000


# ---------------------------------------------------------------------------
# GET /{event_id}
# ---------------------------------------------------------------------------


class TestEventDetail:
    """GET /api/v1/events/{event_id}"""

    @patch("app.routers.events.event_service.get_event_by_id", new_callable=AsyncMock)
    def test_detail_returns_200(self, mock_detail, client):
        ev = _fake_event()
        mock_detail.return_value = ev
        resp = client.get(f"/api/v1/events/{ev.id}")
        assert resp.status_code == 200

    @patch("app.routers.events.event_service.get_event_by_id", new_callable=AsyncMock)
    def test_detail_response_has_event_fields(self, mock_detail, client):
        ev = _fake_event(title="Jazz Night")
        mock_detail.return_value = ev
        data = client.get(f"/api/v1/events/{ev.id}").json()
        assert data["title"] == "Jazz Night"
        assert "venue" in data
        assert "category" in data


# ---------------------------------------------------------------------------
# POST /{event_id}/swipe
# ---------------------------------------------------------------------------


class TestSwipeEndpoint:
    """POST /api/v1/events/{event_id}/swipe"""

    @patch("app.routers.events.event_service.record_swipe", new_callable=AsyncMock)
    def test_swipe_right_returns_200(self, mock_swipe, client):
        mock_swipe.return_value = SwipeActionResponse(success=True, message="Swipe right recorded")
        eid = str(uuid.uuid4())
        resp = client.post(f"/api/v1/events/{eid}/swipe", json={"direction": "right"})
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    @patch("app.routers.events.event_service.record_swipe", new_callable=AsyncMock)
    def test_swipe_left_returns_200(self, mock_swipe, client):
        mock_swipe.return_value = SwipeActionResponse(success=True, message="Swipe left recorded")
        eid = str(uuid.uuid4())
        resp = client.post(f"/api/v1/events/{eid}/swipe", json={"direction": "left"})
        assert resp.status_code == 200

    def test_swipe_invalid_direction_returns_422(self, client):
        eid = str(uuid.uuid4())
        resp = client.post(f"/api/v1/events/{eid}/swipe", json={"direction": "up"})
        assert resp.status_code == 422

    def test_swipe_missing_direction_returns_422(self, client):
        eid = str(uuid.uuid4())
        resp = client.post(f"/api/v1/events/{eid}/swipe", json={})
        assert resp.status_code == 422

    def test_swipe_requires_auth(self, unauthed_client):
        eid = str(uuid.uuid4())
        resp = unauthed_client.post(f"/api/v1/events/{eid}/swipe", json={"direction": "right"})
        assert resp.status_code == 401
