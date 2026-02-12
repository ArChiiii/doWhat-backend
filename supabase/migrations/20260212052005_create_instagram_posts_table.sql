-- ============================================================
-- Table: instagram_posts
-- Stores raw Instagram post data scraped via Apify
-- ============================================================
CREATE TABLE public.instagram_posts (
  id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
  instagram_post_id text UNIQUE NOT NULL,  -- shortCode from Apify (e.g. "DTr5_EYEdIH")
  content text,                             -- post caption
  source_url text,                          -- full IG post URL
  scrape_date timestamptz DEFAULT now(),
  processing_status text DEFAULT 'unprocessed'
    CHECK (processing_status IN ('unprocessed', 'processing', 'processed', 'error', 'duplicate')),
  processing_date timestamptz,
  error_message text,
  duplicate_detected boolean DEFAULT false,
  instagram_username text,
  hashtags text[] DEFAULT '{}',
  feature_image_url text,                   -- primary display image URL
  image_urls text[] DEFAULT '{}',           -- all image URLs from the post
  mentions text[] DEFAULT '{}',
  tagged_users text[] DEFAULT '{}',
  remarks text,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

-- Indexes for common queries
CREATE INDEX idx_instagram_posts_username ON public.instagram_posts (instagram_username);
CREATE INDEX idx_instagram_posts_processing_status ON public.instagram_posts (processing_status);
CREATE INDEX idx_instagram_posts_scrape_date ON public.instagram_posts (scrape_date DESC);

-- Comments
COMMENT ON TABLE public.instagram_posts IS 'Raw Instagram posts scraped via Apify, processed by AI to extract events';
COMMENT ON COLUMN public.instagram_posts.instagram_post_id IS 'Instagram shortCode (unique per post), used as dedup key';
COMMENT ON COLUMN public.instagram_posts.processing_status IS 'Pipeline status: unprocessed → processing → processed/error/duplicate';
