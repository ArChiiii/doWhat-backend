-- Initial database schema for doWhat app
-- This migration creates all core tables: users, user_preferences, events, swipe_history, interested_events, scraper_logs

-- ============================================================================
-- Table: users
-- Purpose: Store user account information (managed by Supabase Auth)
-- ============================================================================
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    email_verified BOOLEAN DEFAULT FALSE,
    auth_provider VARCHAR(50) DEFAULT 'email', -- 'email' | 'google'
    auth_provider_id VARCHAR(255), -- OAuth ID if social login
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_login_at TIMESTAMP,
    CONSTRAINT valid_email CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$'),
    CONSTRAINT valid_auth_provider CHECK (auth_provider IN ('email', 'google'))
);

-- Indexes for users table
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_auth_provider_id ON users(auth_provider_id) WHERE auth_provider_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at DESC);

COMMENT ON TABLE users IS 'User accounts with authentication provider information';
COMMENT ON COLUMN users.email IS 'User email address (unique identifier)';
COMMENT ON COLUMN users.email_verified IS 'Whether email has been verified via confirmation link';
COMMENT ON COLUMN users.auth_provider IS 'Authentication method: email or OAuth provider';
COMMENT ON COLUMN users.auth_provider_id IS 'External OAuth provider user ID (for Google, etc.)';

-- ============================================================================
-- Table: user_preferences
-- Purpose: Store user-specific preferences for event discovery personalization
-- ============================================================================
CREATE TABLE IF NOT EXISTS user_preferences (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    categories TEXT[] DEFAULT '{}', -- Array of category slugs: ['music', 'arts', 'food']
    location_lat DECIMAL(9, 6), -- For "Near Me" filter
    location_lng DECIMAL(9, 6),
    location_enabled BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for user_preferences table
CREATE INDEX IF NOT EXISTS idx_user_preferences_user_id ON user_preferences(user_id);
CREATE INDEX IF NOT EXISTS idx_user_preferences_location ON user_preferences(location_lat, location_lng) WHERE location_enabled = TRUE;

COMMENT ON TABLE user_preferences IS 'User preferences for personalized event recommendations';
COMMENT ON COLUMN user_preferences.categories IS 'Array of preferred event categories';
COMMENT ON COLUMN user_preferences.location_lat IS 'User latitude for proximity-based recommendations';
COMMENT ON COLUMN user_preferences.location_lng IS 'User longitude for proximity-based recommendations';
COMMENT ON COLUMN user_preferences.location_enabled IS 'Whether user has enabled location-based filtering';

-- ============================================================================
-- Table: events
-- Purpose: Store event information scraped from various sources
-- ============================================================================
CREATE TABLE IF NOT EXISTS events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(500) NOT NULL,
    description TEXT,
    event_date TIMESTAMP NOT NULL,
    event_end_date TIMESTAMP, -- For multi-day events
    venue_name VARCHAR(255),
    venue_address TEXT,
    venue_lat DECIMAL(9, 6),
    venue_lng DECIMAL(9, 6),
    category VARCHAR(50), -- 'music' | 'arts' | 'food' | 'sports' | 'nightlife' | 'workshops' | 'outdoor' | 'family'
    price_min INTEGER, -- In HKD cents (e.g., 20000 = HKD 200)
    price_max INTEGER,
    is_free BOOLEAN DEFAULT FALSE,
    image_url TEXT, -- Cloudinary URL
    image_urls TEXT[], -- Array of additional images
    source_name VARCHAR(50), -- 'popticket' | 'eventbrite' | 'discover_hk' | 'manual'
    source_url TEXT, -- External booking link
    booking_url TEXT, -- Direct ticket purchase link
    interest_count INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'active', -- 'active' | 'cancelled' | 'expired'
    scraped_at TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT valid_category CHECK (category IN ('music', 'arts', 'food', 'sports', 'nightlife', 'workshops', 'outdoor', 'family')),
    CONSTRAINT valid_status CHECK (status IN ('active', 'cancelled', 'expired')),
    CONSTRAINT valid_source CHECK (source_name IN ('popticket', 'eventbrite', 'discover_hk', 'manual')),
    CONSTRAINT valid_price CHECK (price_min IS NULL OR price_max IS NULL OR price_min <= price_max)
);

-- Critical indexes for query performance
CREATE INDEX IF NOT EXISTS idx_events_event_date ON events(event_date) WHERE status = 'active';
CREATE INDEX IF NOT EXISTS idx_events_category ON events(category) WHERE status = 'active';
CREATE INDEX IF NOT EXISTS idx_events_status ON events(status);
CREATE INDEX IF NOT EXISTS idx_events_venue_location ON events(venue_lat, venue_lng) WHERE venue_lat IS NOT NULL AND venue_lng IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_events_source_name ON events(source_name);
CREATE INDEX IF NOT EXISTS idx_events_is_free ON events(is_free) WHERE status = 'active';
CREATE INDEX IF NOT EXISTS idx_events_interest_count ON events(interest_count DESC) WHERE status = 'active';

-- Full-text search index for future search feature
CREATE INDEX IF NOT EXISTS idx_events_title_search ON events USING gin(to_tsvector('english', title));
CREATE INDEX IF NOT EXISTS idx_events_description_search ON events USING gin(to_tsvector('english', COALESCE(description, '')));

COMMENT ON TABLE events IS 'Event listings from various sources (scraped or manual)';
COMMENT ON COLUMN events.title IS 'Event title/name';
COMMENT ON COLUMN events.event_date IS 'Event start date and time';
COMMENT ON COLUMN events.event_end_date IS 'Event end date and time (for multi-day events)';
COMMENT ON COLUMN events.category IS 'Event category for filtering and personalization';
COMMENT ON COLUMN events.price_min IS 'Minimum ticket price in HKD cents';
COMMENT ON COLUMN events.price_max IS 'Maximum ticket price in HKD cents';
COMMENT ON COLUMN events.is_free IS 'Whether event is free to attend';
COMMENT ON COLUMN events.interest_count IS 'Number of users who marked interest (right swipe)';
COMMENT ON COLUMN events.status IS 'Event status: active (visible), cancelled, or expired';

-- ============================================================================
-- Table: swipe_history
-- Purpose: Track user swipe actions for personalization algorithm
-- ============================================================================
CREATE TABLE IF NOT EXISTS swipe_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    event_id UUID NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    direction VARCHAR(10) NOT NULL, -- 'left' | 'right'
    swiped_at TIMESTAMP DEFAULT NOW(),
    session_id UUID, -- Track which session this swipe occurred in
    CONSTRAINT valid_direction CHECK (direction IN ('left', 'right')),
    UNIQUE(user_id, event_id) -- One swipe per event per user
);

-- Indexes for swipe_history table
CREATE INDEX IF NOT EXISTS idx_swipe_history_user_id ON swipe_history(user_id);
CREATE INDEX IF NOT EXISTS idx_swipe_history_event_id ON swipe_history(event_id);
CREATE INDEX IF NOT EXISTS idx_swipe_history_direction ON swipe_history(direction);
CREATE INDEX IF NOT EXISTS idx_swipe_history_swiped_at ON swipe_history(swiped_at DESC);
CREATE INDEX IF NOT EXISTS idx_swipe_history_user_direction ON swipe_history(user_id, direction);

COMMENT ON TABLE swipe_history IS 'User swipe actions for personalization and analytics';
COMMENT ON COLUMN swipe_history.direction IS 'Swipe direction: left (pass) or right (interested)';
COMMENT ON COLUMN swipe_history.session_id IS 'Session identifier for analytics tracking';

-- ============================================================================
-- Table: interested_events
-- Purpose: Store user's interested/saved events (right swipes)
-- ============================================================================
CREATE TABLE IF NOT EXISTS interested_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    event_id UUID NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    interested_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, event_id)
);

-- Indexes for interested_events table
CREATE INDEX IF NOT EXISTS idx_interested_events_user_id ON interested_events(user_id);
CREATE INDEX IF NOT EXISTS idx_interested_events_event_id ON interested_events(event_id);
CREATE INDEX IF NOT EXISTS idx_interested_events_interested_at ON interested_events(interested_at DESC);

COMMENT ON TABLE interested_events IS 'Events that users have marked as interested (right swipe/save)';
COMMENT ON COLUMN interested_events.interested_at IS 'Timestamp when user marked interest';

-- ============================================================================
-- Table: scraper_logs
-- Purpose: Log web scraping jobs for monitoring and debugging
-- ============================================================================
CREATE TABLE IF NOT EXISTS scraper_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_name VARCHAR(50) NOT NULL, -- 'popticket' | 'eventbrite' | 'discover_hk'
    status VARCHAR(20) NOT NULL, -- 'success' | 'failure' | 'running'
    events_scraped INTEGER DEFAULT 0,
    events_new INTEGER DEFAULT 0,
    events_updated INTEGER DEFAULT 0,
    error_message TEXT,
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    duration_seconds INTEGER,
    CONSTRAINT valid_scraper_status CHECK (status IN ('success', 'failure', 'running')),
    CONSTRAINT valid_scraper_source CHECK (source_name IN ('popticket', 'eventbrite', 'discover_hk'))
);

-- Indexes for scraper_logs table
CREATE INDEX IF NOT EXISTS idx_scraper_logs_source_name ON scraper_logs(source_name);
CREATE INDEX IF NOT EXISTS idx_scraper_logs_started_at ON scraper_logs(started_at DESC);
CREATE INDEX IF NOT EXISTS idx_scraper_logs_status ON scraper_logs(status);

COMMENT ON TABLE scraper_logs IS 'Logs for web scraping jobs (for monitoring and debugging)';
COMMENT ON COLUMN scraper_logs.source_name IS 'Source being scraped (popticket, eventbrite, etc.)';
COMMENT ON COLUMN scraper_logs.status IS 'Job status: success, failure, or running';
COMMENT ON COLUMN scraper_logs.events_scraped IS 'Total events processed in this scrape';
COMMENT ON COLUMN scraper_logs.events_new IS 'Number of new events added';
COMMENT ON COLUMN scraper_logs.events_updated IS 'Number of existing events updated';
COMMENT ON COLUMN scraper_logs.duration_seconds IS 'Job execution time in seconds';

-- ============================================================================
-- Initial Data / Seed Data
-- ============================================================================

-- Create default user preferences for all existing users
-- This will be handled by application logic when a user is created
