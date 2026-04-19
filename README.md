# AI Recruiter (Frontend + Backend + Supabase)

Ce projet est maintenant unifie autour de **Supabase** comme base de donnees unique.

## Architecture

- `frontend/` : interface React (CRA + CRACO)
- `backend/` : API FastAPI pour analyse IA et gestion des leads
- Base de donnees : table `leads` dans Supabase (plus de MongoDB)

## Prerequis

- Node.js 18+
- Yarn 1.x
- Python 3.10+

## Configuration

1. Copier le fichier d'exemple:
   - `backend/.env.example` -> `backend/.env`
2. Renseigner les variables Supabase et la cle API LLM.
   - Optionnel: definir `TARGET_DOMAINS` pour prioriser les profils de formateurs selon tes besoins.
   - Securite: la connexion utilise Supabase Auth (utilisateurs crees dans Supabase) avec `SUPABASE_AUTH_KEY` (anon key).
   - Automation agent: definir `PROJECT_URL`, `PROJECT_SIGNUP_URL` et les variables SMTP (`SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM`) pour l'envoi des courriels.
   - Discovery YouTube: definir `YOUTUBE_API_KEY` et (optionnel) `YOUTUBE_DISCOVERY_QUERIES` pour la prospection automatique.
3. Creer la table Supabase en suivant `backend/SUPABASE_MIGRATION.md`.

## Installation des dependances

Depuis la racine:

```bash
npm install
npm run install:all
```

## Demarrage (frontend + backend ensemble)

```bash
npm run dev
```

- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:8000/api`

## Mode unifie (un seul serveur)

Le backend FastAPI peut aussi servir le frontend build React sur **le meme port**.

```bash
npm run start
```

- Application complete: `http://localhost:8000`
- API: `http://localhost:8000/api`
