-- Add schedule JSONB column for recurring event fields
ALTER TABLE events ADD COLUMN IF NOT EXISTS schedule JSONB;

-- Comment on the new column
COMMENT ON COLUMN events.schedule IS 'Recurring event schedule: {has_fixed_hours, opening_time, ending_time, operating_days, is_all_day}';

-- Drop old category constraint and add expanded one
ALTER TABLE events DROP CONSTRAINT IF EXISTS valid_category;
ALTER TABLE events ADD CONSTRAINT valid_category CHECK (
  category IS NULL OR category IN (
    'music', 'arts', 'food', 'sports', 'nightlife',
    'workshops', 'outdoor', 'family',
    'markets', 'theater', 'education', 'festival', 'other'
  )
);

-- Add GIN index on schedule for future queries
CREATE INDEX IF NOT EXISTS idx_events_schedule ON events USING GIN (schedule);
