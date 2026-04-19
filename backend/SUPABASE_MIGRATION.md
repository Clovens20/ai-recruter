Konekte AI Recruiter — Guide migration Supabase
================================================

IMPORTANT — Erreur 42601 avec "#"
---------------------------------
Si Supabase affiche : syntax error at or near "#" LINE 1: # Konekte ...

Cela veut dire que tu as colle le fichier **SUPABASE_MIGRATION.md** (Markdown) dans l’editeur SQL. Postgres n’accepte pas les lignes qui commencent par #.

Ce qu’il faut faire :

1. Dans ton projet, ouvre le fichier **supabase_schema.sql** (meme dossier que ce guide : `backend/supabase_schema.sql`).
2. Selectionne tout le contenu de **supabase_schema.sql** uniquement (Ctrl+A dans ce fichier).
3. Colle dans Supabase : SQL → New query → Run.

Ne copie pas ce fichier .md dans Supabase.

Variables d’environnement (backend)
----------------------------------
SUPABASE_URL=url-du-projet
SUPABASE_KEY=cle-service-role-recommandee
OPENAI_API_KEY=...

Notes
-----
- Le schema SQL executable est maintenu dans **supabase_schema.sql** (une seule source).
- Les requetes API utilisent PostgREST : `/rest/v1/leads`, `/rest/v1/agent_configs`, etc.

Erreur 503 sur /rest/v1/leads — proxy_status: PostgREST; error=PGRST002
-----------------------------------------------------------------------
C’est le **cache schema PostgREST** qui n’est pas encore aligné avec ta base (souvent juste après avoir créé des tables).

1. Va dans **Supabase → SQL → New query**.
2. Exécute **exactement** cette ligne (puis Run) :

```sql
NOTIFY pgrst, 'reload schema';
```

3. Attends **30 à 60 secondes**, puis recharge ton app (Dashboard / agents).

Si tu n’as pas encore relancé tout le script : ré-exécute **`backend/supabase_schema.sql`** en entier — il inclut maintenant cette ligne à la fin.

Si le 503 continue : onglet **Project Settings** (état du projet), ou **Pause project** puis **Restore** pour forcer un redémarrage (plan Free parfois en sommeil). En dernier recours : support Supabase avec l’id de requête (`sb_request_id` / logs).
