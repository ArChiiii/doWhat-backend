-- Database triggers for doWhat app
-- This migration creates triggers for automated tasks:
-- 1. Update updated_at timestamp on record changes
-- 2. Auto-expire past events (via cron job)

-- ============================================================================
-- Trigger Function: Update updated_at timestamp
-- Purpose: Automatically update updated_at column when a record is modified
-- ============================================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION update_updated_at_column() IS 'Automatically updates the updated_at timestamp on row modification';

-- Apply trigger to users table
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Apply trigger to user_preferences table
CREATE TRIGGER update_user_preferences_updated_at
    BEFORE UPDATE ON user_preferences
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Apply trigger to events table
CREATE TRIGGER update_events_updated_at
    BEFORE UPDATE ON events
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- Function: Auto-expire past events
-- Purpose: Mark events as expired when their date has passed
-- Note: This should be called by a cron job daily (pg_cron or application-level)
-- ============================================================================
CREATE OR REPLACE FUNCTION expire_past_events()
RETURNS INTEGER AS $$
DECLARE
    affected_rows INTEGER;
BEGIN
    -- Update events to expired status if event_date is in the past
    -- and they are currently active
    UPDATE events
    SET status = 'expired',
        updated_at = NOW()
    WHERE event_date < NOW() - INTERVAL '1 day'
    AND status = 'active';

    GET DIAGNOSTICS affected_rows = ROW_COUNT;

    -- Log the operation (optional, for debugging)
    RAISE NOTICE 'Expired % past events', affected_rows;

    RETURN affected_rows;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION expire_past_events() IS 'Marks past events as expired. Should be called daily via cron job.';

-- ============================================================================
-- Function: Update event interest count
-- Purpose: Automatically update interest_count when interested_events changes
-- ============================================================================
CREATE OR REPLACE FUNCTION update_event_interest_count()
RETURNS TRIGGER AS $$
BEGIN
    IF (TG_OP = 'INSERT') THEN
        -- Increment interest count when user marks interest
        UPDATE events
        SET interest_count = interest_count + 1
        WHERE id = NEW.event_id;
        RETURN NEW;
    ELSIF (TG_OP = 'DELETE') THEN
        -- Decrement interest count when user removes interest
        UPDATE events
        SET interest_count = GREATEST(interest_count - 1, 0)
        WHERE id = OLD.event_id;
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION update_event_interest_count() IS 'Automatically updates event interest_count when users mark/unmark interest';

-- Apply trigger to interested_events table
CREATE TRIGGER update_interest_count_on_insert
    AFTER INSERT ON interested_events
    FOR EACH ROW
    EXECUTE FUNCTION update_event_interest_count();

CREATE TRIGGER update_interest_count_on_delete
    AFTER DELETE ON interested_events
    FOR EACH ROW
    EXECUTE FUNCTION update_event_interest_count();

-- ============================================================================
-- Function: Create default user preferences
-- Purpose: Automatically create user_preferences record when user is created
-- ============================================================================
CREATE OR REPLACE FUNCTION create_default_user_preferences()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO user_preferences (user_id, categories, location_enabled)
    VALUES (NEW.id, '{}', FALSE)
    ON CONFLICT (user_id) DO NOTHING;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION create_default_user_preferences() IS 'Automatically creates default preferences when a user is created';

-- Apply trigger to users table
CREATE TRIGGER create_user_preferences_on_user_creation
    AFTER INSERT ON users
    FOR EACH ROW
    EXECUTE FUNCTION create_default_user_preferences();

-- ============================================================================
-- Scheduled Jobs (pg_cron)
-- Note: pg_cron needs to be enabled in Supabase project
-- Alternative: Run expire_past_events() via application cron job
-- ============================================================================

-- To enable pg_cron extension (run manually in Supabase SQL editor):
-- CREATE EXTENSION IF NOT EXISTS pg_cron;

-- Schedule daily job to expire past events (runs at 1 AM UTC daily)
-- SELECT cron.schedule(
--     'expire-past-events',
--     '0 1 * * *',
--     $$SELECT expire_past_events();$$
-- );

-- View scheduled jobs:
-- SELECT * FROM cron.job;

-- Unschedule job if needed:
-- SELECT cron.unschedule('expire-past-events');
