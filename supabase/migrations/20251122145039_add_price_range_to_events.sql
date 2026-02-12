-- Add price_range column to events table
-- Migration: 20251122145039_add_price_range_to_events.sql
-- Purpose: Add human-readable price range text for display purposes

-- ============================================================================
-- Add price_range column
-- ============================================================================
ALTER TABLE events 
ADD COLUMN price_range TEXT;

-- Add comment for documentation
COMMENT ON COLUMN events.price_range IS 'Human-readable price range text (e.g., "Free", "$100-$200", "From $50")';


