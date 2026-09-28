-- Lead Scraper — Supabase Setup
-- Paste this into the Supabase SQL Editor and click Run.

-- 1. leads table
CREATE TABLE IF NOT EXISTS leads (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  brand text NOT NULL,           -- 'orv' or 'zien'
  source text NOT NULL,          -- 'maps', 'instagram', 'linkedin'
  name text NOT NULL,
  category text,
  address text,
  city text,
  rating numeric,
  reviews integer,
  website text,
  phone text,
  followers text,
  score integer,
  why text,
  outreach_dm text,
  niche text,
  created_at timestamptz DEFAULT now(),
  UNIQUE (name, address, brand)
);

-- 2. outreach_log table
CREATE TABLE IF NOT EXISTS outreach_log (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  lead_id uuid REFERENCES leads(id) ON DELETE CASCADE,
  brand text,
  dm_text text,
  created_at timestamptz DEFAULT now()
);

-- 3. Indexes
CREATE INDEX IF NOT EXISTS idx_leads_brand ON leads(brand);
CREATE INDEX IF NOT EXISTS idx_leads_source ON leads(source);
CREATE INDEX IF NOT EXISTS idx_leads_score ON leads(score DESC);
CREATE INDEX IF NOT EXISTS idx_leads_created ON leads(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_outreach_log_lead_id ON outreach_log(lead_id);

-- 4. Row Level Security
ALTER TABLE leads ENABLE ROW LEVEL SECURITY;
ALTER TABLE outreach_log ENABLE ROW LEVEL SECURITY;

CREATE POLICY "allow all" ON leads FOR ALL USING (true);
CREATE POLICY "allow all" ON outreach_log FOR ALL USING (true);
