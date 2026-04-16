from fastapi import FastAPI, APIRouter, HTTPException, Query
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import json
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
import uuid
from datetime import datetime, timezone
from emergentintegrations.llm.chat import LlmChat, UserMessage

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# LLM Config
EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY', '')

app = FastAPI()
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ─── Models ───────────────────────────────────────────────────────────────────

class ProfileInput(BaseModel):
    name: str
    bio: str
    platform: str  # facebook, tiktok, youtube
    followers: int
    content_example: str

class ProfileAnalysis(BaseModel):
    is_educator: bool
    domain: str
    potential: str  # faible, moyen, eleve
    score: int  # 0-100
    reasoning: str

class LeadResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    name: str
    bio: str
    platform: str
    followers: int
    content_example: str
    is_educator: bool
    domain: str
    potential: str
    score: int
    reasoning: str
    generated_message: str
    status: str
    created_at: str

class LeadStatusUpdate(BaseModel):
    status: str  # new, contacted, replied

class StatsResponse(BaseModel):
    total: int
    by_status: dict
    by_platform: dict
    avg_score: float
    high_potential: int
    medium_potential: int
    low_potential: int

# ─── AI Service ───────────────────────────────────────────────────────────────

ANALYSIS_SYSTEM_PROMPT = """Tu es un expert en recrutement d'educateurs et createurs de contenu pour Konekte Group, une plateforme educative innovante.

Ton role est d'analyser des profils de createurs de contenu et de determiner:
1. Si la personne est un educateur (professeur, coach, formateur, createur de contenu educatif)
2. Son domaine d'expertise
3. Son potentiel de recrutement

Tu dois repondre UNIQUEMENT en JSON valide avec cette structure exacte:
{
  "is_educator": true/false,
  "domain": "le domaine d'expertise (math, business, developpement personnel, tech, langues, sciences, art, fitness, etc.)",
  "potential": "faible" ou "moyen" ou "eleve",
  "score": un nombre entre 0 et 100,
  "reasoning": "explication courte de ton analyse"
}

Criteres de scoring:
- Nombre d'abonnes: >100k = +30pts, >10k = +20pts, >1k = +10pts
- Contenu educatif clair = +25pts
- Bio professionnelle = +15pts
- Plateforme adaptee (YouTube > TikTok > Facebook pour l'education) = +10pts
- Engagement potentiel = +20pts"""

MESSAGE_SYSTEM_PROMPT = """Tu es un expert en communication et recrutement pour Konekte Group, une plateforme educative innovante en Haiti et dans le monde francophone.

Tu dois generer un message de recrutement personnalise, naturel et non-spam.

Le message DOIT:
- Mentionner un element specifique du contenu de la personne
- Presenter Konekte Group comme une opportunite excitante
- Etre chaleureux et professionnel
- Inviter a discuter sans pression
- Etre en francais
- Faire entre 3 et 5 phrases maximum

Reponds UNIQUEMENT avec le texte du message, sans guillemets ni formatage supplementaire."""


async def analyze_profile_with_ai(profile: ProfileInput) -> dict:
    """Use AI to analyze a profile and determine educator potential."""
    try:
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"analysis-{uuid.uuid4()}",
            system_message=ANALYSIS_SYSTEM_PROMPT
        ).with_model("openai", "gpt-4o")

        user_msg = UserMessage(
            text=f"""Analyse ce profil:
- Nom: {profile.name}
- Bio: {profile.bio}
- Plateforme: {profile.platform}
- Abonnes: {profile.followers}
- Exemple de contenu: {profile.content_example}"""
        )

        response = await chat.send_message(user_msg)
        # Parse JSON from response
        cleaned = response.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()

        analysis = json.loads(cleaned)
        return analysis
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse AI analysis response: {e}")
        # Fallback analysis
        score = min(100, max(0, profile.followers // 1000 + 30))
        return {
            "is_educator": True,
            "domain": "general",
            "potential": "moyen" if score > 40 else "faible",
            "score": score,
            "reasoning": "Analyse automatique basee sur les metriques du profil."
        }
    except Exception as e:
        logger.error(f"AI analysis error: {e}")
        score = min(100, max(0, profile.followers // 1000 + 30))
        return {
            "is_educator": True,
            "domain": "general",
            "potential": "moyen" if score > 40 else "faible",
            "score": score,
            "reasoning": "Analyse automatique basee sur les metriques du profil."
        }


async def generate_recruitment_message(profile: ProfileInput, analysis: dict) -> str:
    """Use AI to generate a personalized recruitment message."""
    try:
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"message-{uuid.uuid4()}",
            system_message=MESSAGE_SYSTEM_PROMPT
        ).with_model("openai", "gpt-4o")

        user_msg = UserMessage(
            text=f"""Genere un message de recrutement pour cette personne:
- Nom: {profile.name}
- Plateforme: {profile.platform}
- Domaine: {analysis.get('domain', 'education')}
- Contenu: {profile.content_example}
- Score: {analysis.get('score', 50)}/100"""
        )

        response = await chat.send_message(user_msg)
        return response.strip()
    except Exception as e:
        logger.error(f"Message generation error: {e}")
        return f"Bonjour {profile.name}, votre contenu sur {profile.platform} est remarquable! Konekte Group cherche des talents comme vous pour rejoindre notre plateforme educative. Seriez-vous disponible pour en discuter?"


# ─── Routes ───────────────────────────────────────────────────────────────────

@api_router.get("/")
async def root():
    return {"message": "Konekte AI Recruiter Agent API"}


@api_router.post("/analyze-profile", response_model=LeadResponse)
async def analyze_profile(profile: ProfileInput):
    """Analyze a profile using AI and save as a lead."""
    # AI Analysis
    analysis = await analyze_profile_with_ai(profile)

    # Generate recruitment message
    message = await generate_recruitment_message(profile, analysis)

    # Create lead document
    lead_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    lead_doc = {
        "id": lead_id,
        "name": profile.name,
        "bio": profile.bio,
        "platform": profile.platform.lower(),
        "followers": profile.followers,
        "content_example": profile.content_example,
        "is_educator": analysis.get("is_educator", False),
        "domain": analysis.get("domain", "general"),
        "potential": analysis.get("potential", "moyen"),
        "score": analysis.get("score", 50),
        "reasoning": analysis.get("reasoning", ""),
        "generated_message": message,
        "status": "new",
        "created_at": now
    }

    await db.leads.insert_one(lead_doc)

    return LeadResponse(**lead_doc)


@api_router.get("/leads", response_model=List[LeadResponse])
async def get_leads(
    status: Optional[str] = Query(None),
    platform: Optional[str] = Query(None),
    min_score: Optional[int] = Query(None),
    max_score: Optional[int] = Query(None),
):
    """Get all leads with optional filtering."""
    query = {}
    if status:
        query["status"] = status
    if platform:
        query["platform"] = platform.lower()
    if min_score is not None or max_score is not None:
        score_filter = {}
        if min_score is not None:
            score_filter["$gte"] = min_score
        if max_score is not None:
            score_filter["$lte"] = max_score
        query["score"] = score_filter

    leads = await db.leads.find(query, {"_id": 0}).sort("created_at", -1).to_list(500)
    return leads


@api_router.patch("/leads/{lead_id}/status")
async def update_lead_status(lead_id: str, update: LeadStatusUpdate):
    """Update the status of a lead."""
    if update.status not in ["new", "contacted", "replied"]:
        raise HTTPException(status_code=400, detail="Status must be: new, contacted, or replied")

    result = await db.leads.update_one(
        {"id": lead_id},
        {"$set": {"status": update.status}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Lead not found")

    return {"message": "Status updated", "id": lead_id, "status": update.status}


@api_router.delete("/leads/{lead_id}")
async def delete_lead(lead_id: str):
    """Delete a lead."""
    result = await db.leads.delete_one({"id": lead_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Lead not found")
    return {"message": "Lead deleted", "id": lead_id}


@api_router.get("/leads/stats", response_model=StatsResponse)
async def get_leads_stats():
    """Get dashboard statistics."""
    all_leads = await db.leads.find({}, {"_id": 0, "status": 1, "platform": 1, "score": 1, "potential": 1}).to_list(1000)

    total = len(all_leads)
    by_status = {}
    by_platform = {}
    total_score = 0
    high = medium = low = 0

    for lead in all_leads:
        s = lead.get("status", "new")
        by_status[s] = by_status.get(s, 0) + 1

        p = lead.get("platform", "unknown")
        by_platform[p] = by_platform.get(p, 0) + 1

        total_score += lead.get("score", 0)

        pot = lead.get("potential", "moyen")
        if pot == "eleve":
            high += 1
        elif pot == "moyen":
            medium += 1
        else:
            low += 1

    return StatsResponse(
        total=total,
        by_status=by_status,
        by_platform=by_platform,
        avg_score=round(total_score / total, 1) if total > 0 else 0,
        high_potential=high,
        medium_potential=medium,
        low_potential=low
    )


@api_router.post("/leads/{lead_id}/regenerate-message")
async def regenerate_message(lead_id: str):
    """Regenerate the recruitment message for an existing lead."""
    lead = await db.leads.find_one({"id": lead_id}, {"_id": 0})
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    profile = ProfileInput(
        name=lead["name"],
        bio=lead["bio"],
        platform=lead["platform"],
        followers=lead["followers"],
        content_example=lead["content_example"]
    )

    analysis = {
        "domain": lead.get("domain", "general"),
        "score": lead.get("score", 50)
    }

    new_message = await generate_recruitment_message(profile, analysis)

    await db.leads.update_one(
        {"id": lead_id},
        {"$set": {"generated_message": new_message}}
    )

    return {"message": new_message, "id": lead_id}


# Include router and middleware
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
