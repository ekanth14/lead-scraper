-- Lead Scraper - Supabase SQL Setup
-- Dual-brand Lead Scraper for "orv" and "zien"

-- 1. Free-Tier Guard: usage table
CREATE TABLE IF NOT EXISTS usage (
    month text PRIMARY KEY,
    calls integer NOT NULL DEFAULT 0
);

-- RPC for atomic usage increment
CREATE OR REPLACE FUNCTION increment_usage(p_month text, p_count int)
RETURNS int AS $$
DECLARE
    v_calls int;
BEGIN
    INSERT INTO usage (month, calls)
    VALUES (p_month, p_count)
    ON CONFLICT (month)
    DO UPDATE SET calls = usage.calls + p_count
    RETURNING calls INTO v_calls;
    RETURN v_calls;
END;
$$ LANGUAGE plpgsql;

-- 2. leads table
CREATE TABLE IF NOT EXISTS leads (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    place_id text UNIQUE NOT NULL,
    brand text NOT NULL,              -- 'orv' or 'zien'
    niche text,
    name text NOT NULL,
    address text,
    phone text,
    website text,
    website_status text NOT NULL DEFAULT 'none',  -- 'none', 'social_only', 'has_website'
    rating numeric,
    reviews integer,
    score integer NOT NULL DEFAULT 40,
    label text NOT NULL DEFAULT 'cold',           -- 'hot', 'warm', 'cold'
    why text,
    maps_url text,
    source text DEFAULT 'maps',
    category text,
    city text,
    followers text,
    outreach_dm text,
    created_at timestamptz DEFAULT now()
);

-- 3. Indexes for fast filtering and ranking
CREATE INDEX IF NOT EXISTS idx_leads_place_id ON leads(place_id);
CREATE INDEX IF NOT EXISTS idx_leads_brand ON leads(brand);
CREATE INDEX IF NOT EXISTS idx_leads_website_status ON leads(website_status);
CREATE INDEX IF NOT EXISTS idx_leads_label ON leads(label);
CREATE INDEX IF NOT EXISTS idx_leads_score ON leads(score DESC);
CREATE INDEX IF NOT EXISTS idx_leads_created ON leads(created_at DESC);

-- 4. Row Level Security (RLS)
ALTER TABLE usage ENABLE ROW LEVEL SECURITY;
ALTER TABLE leads ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "allow all usage" ON usage;
CREATE POLICY "allow all usage" ON usage FOR ALL USING (true);

DROP POLICY IF EXISTS "allow all leads" ON leads;
CREATE POLICY "allow all leads" ON leads FOR ALL USING (true);
