-- ============================================================
-- RLS policies for instagram_posts
-- n8n uses service_role key, so it bypasses RLS automatically.
-- Regular users can only read processed posts.
-- ============================================================

ALTER TABLE public.instagram_posts ENABLE ROW LEVEL SECURITY;

-- Authenticated/anon users can only see processed posts
CREATE POLICY "Anyone can read processed instagram posts"
  ON public.instagram_posts
  FOR SELECT
  USING (processing_status = 'processed');

-- n8n will use service_role key which bypasses RLS
-- No insert/update/delete policies needed for regular users
