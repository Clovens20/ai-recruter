# Konekte AI Recruiter Agent - PRD

## Problem Statement
Build an AI-powered recruitment platform for Konekte Group to automatically recruit teachers, coaches, and educational content creators from the internet.

## Architecture
- **Backend**: FastAPI (Python) + MongoDB + emergentintegrations (OpenAI GPT-4o)
- **Frontend**: React + Shadcn UI + Tailwind CSS (dark theme) + Framer Motion
- **Database**: MongoDB (with Supabase migration guide ready)
- **AI**: OpenAI GPT-4o via Emergent LLM key

## User Personas
- Konekte Group recruiters managing educator leads
- Platform administrators tracking recruitment pipeline

## Core Requirements
- AI profile analysis (educator detection, domain, score)
- Personalized recruitment message generation
- Leads management dashboard with CRUD operations
- Status tracking (new → contacted → replied)
- Filtering by score, status, platform

## What's Been Implemented (Feb 2026)
### Backend
- POST /api/analyze-profile - AI profile analysis + message generation
- GET /api/leads - List leads with filtering (status, platform, score)
- GET /api/leads/stats - Dashboard statistics
- PATCH /api/leads/{id}/status - Update lead status
- DELETE /api/leads/{id} - Delete lead
- POST /api/leads/{id}/regenerate-message - Regenerate AI message

### Frontend
- Dashboard with stats cards (total leads, avg score, high potential, pending)
- Leads table with filtering (status, platform) and score sorting
- Profile analyzer form with AI analysis results
- Message dialog with copy and regenerate functionality
- Sidebar navigation
- Dark AI theme with Outfit + IBM Plex Sans fonts
- Framer Motion animations

### Database
- MongoDB leads collection with all required fields
- Supabase migration guide at /app/backend/SUPABASE_MIGRATION.md

## Prioritized Backlog
### P0 (Critical)
- None remaining

### P1 (Important)
- Bulk profile import (CSV/JSON)
- Email integration for sending messages
- Webhook notifications for status changes

### P2 (Nice to have)
- Analytics dashboard with charts
- Multi-user support with authentication
- Automated web scraping for profile discovery
- A/B testing for recruitment messages
- Export leads to CSV

## Next Tasks
1. Connect Supabase when user provides credentials
2. Add authentication if needed
3. Add bulk import functionality
4. Add analytics/charts to dashboard
