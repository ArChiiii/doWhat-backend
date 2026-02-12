-- ============================================================
-- Drop old restrictive CHECK constraints on events table
-- These duplicated the newer expanded constraints from
-- 20260212052020_expand_events_for_instagram_pipeline.sql
-- ============================================================

ALTER TABLE public.events DROP CONSTRAINT IF EXISTS valid_source;
ALTER TABLE public.events DROP CONSTRAINT IF EXISTS valid_status;
