# Konekte AI Recruiter - Supabase Migration Guide

## SQL Schema for Supabase

```sql
-- Create leads table
CREATE TABLE leads (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  bio TEXT NOT NULL,
  platform TEXT NOT NULL CHECK (platform IN ('youtube', 'tiktok', 'facebook')),
  followers INTEGER DEFAULT 0,
  content_example TEXT,
  is_educator BOOLEAN DEFAULT false,
  domain TEXT DEFAULT 'general',
  potential TEXT CHECK (potential IN ('faible', 'moyen', 'eleve')),
  score INTEGER DEFAULT 0 CHECK (score >= 0 AND score <= 100),
  reasoning TEXT,
  generated_message TEXT,
  status TEXT DEFAULT 'new' CHECK (status IN ('new', 'contacted', 'replied')),
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Create indexes for common queries
CREATE INDEX idx_leads_status ON leads(status);
CREATE INDEX idx_leads_platform ON leads(platform);
CREATE INDEX idx_leads_score ON leads(score DESC);
CREATE INDEX idx_leads_created_at ON leads(created_at DESC);

-- Enable Row Level Security (optional, for multi-tenant)
ALTER TABLE leads ENABLE ROW LEVEL SECURITY;
```

## Environment Variables to Add
```
SUPABASE_URL=your-supabase-project-url
SUPABASE_KEY=your-supabase-anon-key
```

## Migration Notes
- Replace MongoDB motor client with supabase-py client
- Replace find/insert_one/update_one with supabase.table('leads').select/insert/update
- UUID generation is handled by Supabase (gen_random_uuid)
- Timestamps are handled by Supabase (now())
