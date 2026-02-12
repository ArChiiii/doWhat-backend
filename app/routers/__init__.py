"""
API routers for different endpoint groups.
"""

from .auth import router as auth_router
from .events import router as events_router
from .saved_events import router as saved_events_router

__all__ = ["auth_router", "events_router", "saved_events_router"]
