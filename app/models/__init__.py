# Import all models here for Alembic to detect them
from app.models.user import User
from app.models.event import Event
from app.models.swipe import SwipeHistory
from app.models.interested_event import InterestedEvent
from app.models.user_preferences import UserPreferences
from app.models.scraper_log import ScraperLog

__all__ = [
    "User",
    "Event",
    "SwipeHistory",
    "InterestedEvent",
    "UserPreferences",
    "ScraperLog",
]
