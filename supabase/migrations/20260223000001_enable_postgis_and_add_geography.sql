-- Migration: Enable PostGIS and add geography column with spatial index
-- Purpose: Add PostGIS extension for performant distance queries using spatial indexes
-- Created: 2026-02-23

-- 1. Enable PostGIS extension
CREATE EXTENSION IF NOT EXISTS postgis;

-- 2. Add geography column to events table
ALTER TABLE events ADD COLUMN IF NOT EXISTS venue_location GEOGRAPHY(POINT, 4326);

-- 3. Populate geography column from existing lat/lng values
-- Note: ST_MakePoint takes (longitude, latitude) order
UPDATE events
SET venue_location = ST_SetSRID(ST_MakePoint(venue_lng::double precision, venue_lat::double precision), 4326)::geography
WHERE venue_lat IS NOT NULL
  AND venue_lng IS NOT NULL
  AND venue_location IS NULL;

-- 4. Create trigger function to auto-populate venue_location when lat/lng are inserted/updated
CREATE OR REPLACE FUNCTION update_venue_location()
RETURNS TRIGGER AS $$
BEGIN
  IF NEW.venue_lat IS NOT NULL AND NEW.venue_lng IS NOT NULL THEN
    NEW.venue_location := ST_SetSRID(ST_MakePoint(NEW.venue_lng::double precision, NEW.venue_lat::double precision), 4326)::geography;
  ELSE
    NEW.venue_location := NULL;
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_update_venue_location
BEFORE INSERT OR UPDATE OF venue_lat, venue_lng ON events
FOR EACH ROW EXECUTE FUNCTION update_venue_location();

-- 5. Create GiST spatial index (partial - only active/draft events)
CREATE INDEX IF NOT EXISTS idx_events_venue_location_gist
ON events USING GIST(venue_location)
WHERE status IN ('active', 'draft');

-- 6. Drop the old non-spatial B-tree index on lat/lng (superseded by GiST index)
DROP INDEX IF EXISTS idx_events_venue_location;
