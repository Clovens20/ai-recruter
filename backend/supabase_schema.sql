-- =============================================================================
-- SUPABASE SQL : colle UNIQUEMENT ce fichier dans SQL Editor > Run.
-- Ne PAS coller SUPABASE_MIGRATION.md (erreur 42601 si ligne commence par #).
-- =============================================================================

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE IF NOT EXISTS leads (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  email TEXT,
  bio TEXT NOT NULL,
  platform TEXT NOT NULL CHECK (platform IN ('youtube', 'tiktok', 'facebook', 'instagram')),
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

CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(status);
CREATE INDEX IF NOT EXISTS idx_leads_platform ON leads(platform);
CREATE INDEX IF NOT EXISTS idx_leads_score ON leads(score DESC);
CREATE INDEX IF NOT EXISTS idx_leads_created_at ON leads(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_leads_email ON leads(email);

CREATE TABLE IF NOT EXISTS agent_configs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  function_type TEXT NOT NULL,
  enabled BOOLEAN DEFAULT true,
  settings JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_by TEXT,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_agent_configs_enabled ON agent_configs(enabled);
CREATE INDEX IF NOT EXISTS idx_agent_configs_created_at ON agent_configs(created_at DESC);

CREATE TABLE IF NOT EXISTS agent_runs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  agent_id UUID REFERENCES agent_configs(id) ON DELETE SET NULL,
  agent_name TEXT,
  status TEXT NOT NULL,
  run_type TEXT,
  summary TEXT,
  details JSONB NOT NULL DEFAULT '{}'::jsonb,
  triggered_by TEXT,
  started_at TIMESTAMPTZ DEFAULT now(),
  finished_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_agent_runs_started_at ON agent_runs(started_at DESC);

-- PostgREST: apres CREATE/ALTER, le cache schema peut rester vide (erreur PGRST002, HTTP 503 sur /rest/v1/leads).
-- Cette commande demande a PostgREST de recharger le schema (corrige souvent le 503 dans les logs Supabase).
NOTIFY pgrst, 'reload schema';
