-- Row Level Security (RLS) policies for doWhat app
-- This migration enables RLS and creates security policies for all tables

-- ============================================================================
-- Enable Row Level Security on all tables
-- ============================================================================

-- Enable RLS on users table
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

-- Enable RLS on user_preferences table
ALTER TABLE user_preferences ENABLE ROW LEVEL SECURITY;

-- Enable RLS on events table
ALTER TABLE events ENABLE ROW LEVEL SECURITY;

-- Enable RLS on swipe_history table
ALTER TABLE swipe_history ENABLE ROW LEVEL SECURITY;

-- Enable RLS on interested_events table
ALTER TABLE interested_events ENABLE ROW LEVEL SECURITY;

-- Enable RLS on scraper_logs table
ALTER TABLE scraper_logs ENABLE ROW LEVEL SECURITY;

-- ============================================================================
-- RLS Policies for users table
-- ============================================================================

-- Users can view their own profile
CREATE POLICY "Users can view own profile" ON users
    FOR SELECT USING (auth.uid() = id);

-- Users can update their own profile
CREATE POLICY "Users can update own profile" ON users
    FOR UPDATE USING (auth.uid() = id);

-- Users can insert their own profile (for signup)
CREATE POLICY "Users can insert own profile" ON users
    FOR INSERT WITH CHECK (auth.uid() = id);

-- Users cannot delete their own profile (handled by Supabase Auth)
-- CREATE POLICY "Users can delete own profile" ON users
--     FOR DELETE USING (auth.uid() = id);

-- ============================================================================
-- RLS Policies for user_preferences table
-- ============================================================================

-- Users can view their own preferences
CREATE POLICY "Users can view own preferences" ON user_preferences
    FOR SELECT USING (auth.uid() = user_id);

-- Users can update their own preferences
CREATE POLICY "Users can update own preferences" ON user_preferences
    FOR UPDATE USING (auth.uid() = user_id);

-- Users can insert their own preferences
CREATE POLICY "Users can insert own preferences" ON user_preferences
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Users can delete their own preferences
CREATE POLICY "Users can delete own preferences" ON user_preferences
    FOR DELETE USING (auth.uid() = user_id);

-- ============================================================================
-- RLS Policies for events table
-- ============================================================================

-- Everyone can view active events (public data)
CREATE POLICY "Everyone can view active events" ON events
    FOR SELECT USING (status = 'active');

-- Only authenticated users can view all events (including cancelled/expired)
CREATE POLICY "Authenticated users can view all events" ON events
    FOR SELECT USING (auth.role() = 'authenticated');

-- Only service role can insert/update/delete events (for scrapers)
CREATE POLICY "Service role can manage events" ON events
    FOR ALL USING (auth.role() = 'service_role');

-- ============================================================================
-- RLS Policies for swipe_history table
-- ============================================================================

-- Users can view their own swipe history
CREATE POLICY "Users can view own swipe history" ON swipe_history
    FOR SELECT USING (auth.uid() = user_id);

-- Users can insert their own swipe history
CREATE POLICY "Users can insert own swipe history" ON swipe_history
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Users can update their own swipe history
CREATE POLICY "Users can update own swipe history" ON swipe_history
    FOR UPDATE USING (auth.uid() = user_id);

-- Users can delete their own swipe history
CREATE POLICY "Users can delete own swipe history" ON swipe_history
    FOR DELETE USING (auth.uid() = user_id);

-- ============================================================================
-- RLS Policies for interested_events table
-- ============================================================================

-- Users can view their own event interests
CREATE POLICY "Users can view own event interests" ON interested_events
    FOR SELECT USING (auth.uid() = user_id);

-- Users can insert their own event interests
CREATE POLICY "Users can insert own event interests" ON interested_events
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Users can update their own event interests
CREATE POLICY "Users can update own event interests" ON interested_events
    FOR UPDATE USING (auth.uid() = user_id);

-- Users can delete their own event interests
CREATE POLICY "Users can delete own event interests" ON interested_events
    FOR DELETE USING (auth.uid() = user_id);

-- ============================================================================
-- RLS Policies for scraper_logs table
-- ============================================================================

-- Only service role can manage scraper logs
CREATE POLICY "Service role can manage scraper logs" ON scraper_logs
    FOR ALL USING (auth.role() = 'service_role');

-- Authenticated users can view scraper logs (for debugging)
CREATE POLICY "Authenticated users can view scraper logs" ON scraper_logs
    FOR SELECT USING (auth.role() = 'authenticated');

-- ============================================================================
-- Additional Security Policies
-- ============================================================================

-- Prevent users from accessing other users' data through joins
-- This is handled by the individual table policies above

-- Allow anonymous users to view public events only
-- This is handled by the "Everyone can view active events" policy above

-- Comments for documentation
COMMENT ON POLICY "Users can view own profile" ON users IS 'Users can only see their own user profile';
COMMENT ON POLICY "Users can view own preferences" ON user_preferences IS 'Users can only access their own preferences';
COMMENT ON POLICY "Everyone can view active events" ON events IS 'Public access to active events for discovery';
COMMENT ON POLICY "Service role can manage events" ON events IS 'Only backend services can create/update events';
COMMENT ON POLICY "Users can view own swipe history" ON swipe_history IS 'Users can only see their own swipe history';
COMMENT ON POLICY "Users can view own event interests" ON interested_events IS 'Users can only see their own event interests';
COMMENT ON POLICY "Service role can manage scraper logs" ON scraper_logs IS 'Only backend services can manage scraper logs';
