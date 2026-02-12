-- ============================================================
-- Expand events table for Instagram scraping pipeline
-- ============================================================

-- 1. Add categories array column (keeps existing single 'category' for backward compat)
ALTER TABLE public.events
  ADD COLUMN IF NOT EXISTS categories text[] DEFAULT '{}';

COMMENT ON COLUMN public.events.categories IS 'Array of event categories (from AI extraction). Supercedes single category column.';

-- 2. Add FK to instagram_posts (nullable - not all events come from IG)
ALTER TABLE public.events
  ADD COLUMN IF NOT EXISTS instagram_post_id uuid REFERENCES public.instagram_posts(id) ON DELETE SET NULL;

COMMENT ON COLUMN public.events.instagram_post_id IS 'Link to source Instagram post (if event was extracted from IG)';

-- 3. Add processing_datetime for pipeline tracking
ALTER TABLE public.events
  ADD COLUMN IF NOT EXISTS processing_datetime timestamptz;

COMMENT ON COLUMN public.events.processing_datetime IS 'When the AI extraction processed this event';

-- 4. Expand source_name CHECK to include instagram
ALTER TABLE public.events DROP CONSTRAINT IF EXISTS events_source_name_check;
ALTER TABLE public.events
  ADD CONSTRAINT events_source_name_check
  CHECK (source_name IS NULL OR source_name IN ('popticket', 'eventbrite', 'discover_hk', 'instagram', 'manual'));

-- 5. Expand status CHECK to include draft, published, archived, past
ALTER TABLE public.events DROP CONSTRAINT IF EXISTS events_status_check;
ALTER TABLE public.events
  ADD CONSTRAINT events_status_check
  CHECK (status IS NULL OR status IN ('active', 'draft', 'published', 'cancelled', 'expired', 'archived', 'past'));

-- 6. Index on instagram_post_id for joins
CREATE INDEX IF NOT EXISTS idx_events_instagram_post_id ON public.events (instagram_post_id);

-- 7. Index on categories using GIN for array contains queries
CREATE INDEX IF NOT EXISTS idx_events_categories ON public.events USING gin (categories);
