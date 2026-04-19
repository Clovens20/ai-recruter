from fastapi import BackgroundTasks, FastAPI, APIRouter, HTTPException, Query, Depends, status
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
import os
import asyncio
import logging
import json
import requests
import re
import smtplib
import time
from pathlib import Path
from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional, Dict, Any
from openai import AsyncOpenAI
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from email.message import EmailMessage
from uuid import uuid4
from datetime import datetime, timezone

ROOT_DIR = Path(__file__).resolve().parent
REPO_ROOT = ROOT_DIR.parent
# Racine du depot en premier (ex. C:\...\ai-recruter\.env), puis backend/.env pour surcharges locales
load_dotenv(REPO_ROOT / ".env")
load_dotenv(ROOT_DIR / ".env")

# Supabase connection (PostgREST API)
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")
SUPABASE_REST_URL = f"{SUPABASE_URL.rstrip('/')}/rest/v1" if SUPABASE_URL else ""
SUPABASE_AUTH_URL = f"{SUPABASE_URL.rstrip('/')}/auth/v1" if SUPABASE_URL else ""
SUPABASE_AUTH_KEY = os.environ.get("SUPABASE_AUTH_KEY", SUPABASE_KEY)

# LLM Config
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
AGENT_LLM_MODEL = os.environ.get("OPENAI_AGENT_MODEL", "gpt-4o")
openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

try:
    from . import agent_recruiter as agent_rc
except ImportError:
    import agent_recruiter as agent_rc
PROJECT_URL = os.environ.get("PROJECT_URL", "https://www.konektegroup.com")
PROJECT_SIGNUP_URL = os.environ.get("PROJECT_SIGNUP_URL", "https://www.konektegroup.com")
SMTP_HOST = os.environ.get("SMTP_HOST", "")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
SMTP_FROM = os.environ.get("SMTP_FROM", SMTP_USER or "noreply@konektegroup.com")
YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY", "")
YOUTUBE_DISCOVERY_QUERIES = [
    q.strip()
    for q in os.environ.get(
        "YOUTUBE_DISCOVERY_QUERIES",
        "haitian educator,haitian coach,haitian teacher,kreyol edikasyon,haitian business coach",
    ).split(",")
    if q.strip()
]
TARGET_DOMAINS = [
    d.strip().lower()
    for d in os.environ.get(
        "TARGET_DOMAINS",
        "math,sciences,langues,tech,business,developpement personnel",
    ).split(",")
    if d.strip()
]

app = FastAPI()
api_router = APIRouter(prefix="/api")
auth_router = APIRouter(prefix="/api/auth")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
if not SUPABASE_URL or not SUPABASE_KEY:
    logger.warning("SUPABASE_URL or SUPABASE_KEY is missing. Some data endpoints will use in-memory fallback.")

FRONTEND_BUILD_DIR = REPO_ROOT / "frontend" / "build"
security_scheme = HTTPBearer(auto_error=False)

# Fallback memoire quand Supabase / PostgREST indisponible (ex. PGRST002, plan Free)
OFFLINE_LEADS: List[Dict[str, Any]] = []
OFFLINE_AGENT_CONFIGS: List[Dict[str, Any]] = []
OFFLINE_AGENT_RUNS: List[Dict[str, Any]] = []

# Agents kreye an lokall (fallback) — persist apre restart serveur
OFFLINE_AGENTS_JSON = ROOT_DIR / ".offline_agents.json"


def _load_offline_agent_configs_from_disk() -> None:
    if not OFFLINE_AGENTS_JSON.is_file():
        return
    try:
        raw = OFFLINE_AGENTS_JSON.read_text(encoding="utf-8")
        data = json.loads(raw)
        if isinstance(data, list):
            OFFLINE_AGENT_CONFIGS.clear()
            OFFLINE_AGENT_CONFIGS.extend(data)
            logger.info("Chaje %s agent(s) depi %s", len(OFFLINE_AGENT_CONFIGS), OFFLINE_AGENTS_JSON.name)
    except Exception as e:
        logger.warning("Pa ka chaje %s: %s", OFFLINE_AGENTS_JSON, e)


def _persist_offline_agent_configs() -> None:
    try:
        OFFLINE_AGENTS_JSON.write_text(
            json.dumps(OFFLINE_AGENT_CONFIGS, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except Exception as e:
        logger.warning("Pa ka anrejistre agents offline: %s", e)


def _prune_offline_agents_that_exist_remotely(remote_rows: List[Dict[str, Any]]) -> None:
    """Si Supabase retounen yon agent, retire kopi stale nan fichye offline (menm id)."""
    if not remote_rows:
        return
    rids = {str(r.get("id")) for r in remote_rows if r.get("id")}
    before = len(OFFLINE_AGENT_CONFIGS)
    OFFLINE_AGENT_CONFIGS[:] = [c for c in OFFLINE_AGENT_CONFIGS if str(c.get("id")) not in rids]
    if len(OFFLINE_AGENT_CONFIGS) < before:
        _persist_offline_agent_configs()


def _merge_remote_and_offline_agent_configs(remote: Optional[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    """
    Si Supabase reponn [] (tab vid), pa pèdi agents ki te kreye an offline.
    Konbine remote + offline (pa id), tri pa created_at desc.
    """
    remote_list: List[Dict[str, Any]] = [] if remote is None else list(remote)
    remote_ids = {str(r.get("id")) for r in remote_list if r.get("id")}
    merged = list(remote_list)
    for c in OFFLINE_AGENT_CONFIGS:
        cid = str(c.get("id", ""))
        if cid and cid not in remote_ids:
            merged.append(c)
    merged.sort(key=lambda x: str(x.get("created_at") or x.get("updated_at") or ""), reverse=True)
    return merged


_load_offline_agent_configs_from_disk()


def _is_transient_supabase_failure(exc: BaseException) -> bool:
    if isinstance(exc, (requests.Timeout, requests.ConnectionError, OSError)):
        return True
    if isinstance(exc, HTTPException):
        if exc.status_code in (502, 503, 504):
            return True
        d = str(exc.detail or "").lower()
        if "pgrst" in d or "schema cache" in d:
            return True
        if "schema" in d and "does not exist" in d:
            return True
    return False


def _agent_supabase_timeout() -> float:
    """Timeout kout pou agent_configs / agent_runs (kreyasyon rapid, pa 45s bloke)."""
    return max(4.0, min(60.0, float(os.environ.get("SUPABASE_AGENT_HTTP_TIMEOUT", "6"))))


# Kreyasyon agent: repons imedyat an lokal, senkronizasyon Supabase an aryè (pi rapid pou UI)
AGENT_CREATE_OFFLINE_FIRST = os.environ.get("AGENT_CREATE_OFFLINE_FIRST", "1").lower() in (
    "1",
    "true",
    "yes",
)


def _sync_agent_create_to_supabase(agent_id: str, payload: Dict[str, Any]) -> None:
    """Apre kreyasyon rapid offline, eseye INSERT nan Supabase ak menm UUID."""
    if not (SUPABASE_URL and SUPABASE_KEY):
        return
    try:
        ensure_supabase_config()
        body = {**payload, "id": agent_id}
        rows = supabase_request(
            "POST",
            "/agent_configs",
            payload=body,
            request_timeout=float(os.environ.get("SUPABASE_HTTP_TIMEOUT", "30")),
        )
        if not rows:
            return
        server_row = rows[0]
        for i, c in enumerate(OFFLINE_AGENT_CONFIGS):
            if str(c.get("id")) == str(agent_id):
                OFFLINE_AGENT_CONFIGS[i] = server_row
                _persist_offline_agent_configs()
                return
    except Exception as e:
        logger.warning("Sync agent → Supabase (agent rete lokal): %s", e)


def _supabase_try_call(
    method: str,
    path: str,
    params: Optional[dict] = None,
    payload: Optional[dict] = None,
    request_timeout: Optional[float] = None,
) -> Optional[List[Any]]:
    """
    Retounen list JSON si siksè, None si non konfigire oswa erè transitoire.
    Leve HTTPException si erè non-transitoire.
    """
    if not SUPABASE_URL or not SUPABASE_KEY:
        return None
    try:
        return supabase_request(
            method, path, params=params, payload=payload, request_timeout=request_timeout
        ) or []
    except HTTPException as e:
        if _is_transient_supabase_failure(e):
            logger.warning("Supabase indisponible (transitoire), fallback memoire: %s", e.detail)
            return None
        raise
    except (requests.Timeout, requests.ConnectionError, OSError) as e:
        logger.warning("Supabase rezo/timeout, fallback memoire: %s", e)
        return None


def _supabase_try_list(
    method: str, path: str, params: Optional[dict] = None, request_timeout: Optional[float] = None
) -> Optional[List[Any]]:
    return _supabase_try_call(method, path, params=params, payload=None, request_timeout=request_timeout)


def _filter_leads_local(
    leads: List[Dict[str, Any]],
    status: Optional[str],
    platform: Optional[str],
    min_score: Optional[int],
    max_score: Optional[int],
) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for l in leads:
        if status and l.get("status") != status:
            continue
        if platform and str(l.get("platform", "")).lower() != platform.lower():
            continue
        sc = int(l.get("score") or 0)
        if min_score is not None and sc < min_score:
            continue
        if max_score is not None and sc > max_score:
            continue
        out.append(l)
    return out


def ensure_supabase_auth_config():
    if not SUPABASE_AUTH_URL or not SUPABASE_AUTH_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Supabase Auth is not configured. Set SUPABASE_URL and SUPABASE_AUTH_KEY (or SUPABASE_KEY).",
        )


def supabase_auth_headers(bearer_token: Optional[str] = None) -> dict:
    ensure_supabase_auth_config()
    headers = {
        "apikey": SUPABASE_AUTH_KEY,
        "Content-Type": "application/json",
    }
    if bearer_token:
        headers["Authorization"] = f"Bearer {bearer_token}"
    return headers


def require_auth(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme)) -> str:
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
        )
    try:
        response = requests.get(
            f"{SUPABASE_AUTH_URL}/user",
            headers=supabase_auth_headers(credentials.credentials),
            timeout=20,
        )
        if response.status_code >= 400:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token.")
        user = response.json()
        return user.get("email", "") or user.get("id", "")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token.")


def ensure_supabase_config():
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise HTTPException(
            status_code=500,
            detail="Supabase is not configured. Set SUPABASE_URL and SUPABASE_KEY in .env at repo root or in backend/.env.",
        )


def supabase_request(
    method: str,
    path: str,
    params: Optional[dict] = None,
    payload: Optional[dict] = None,
    request_timeout: Optional[float] = None,
):
    ensure_supabase_config()
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }
    url = f"{SUPABASE_REST_URL}{path}"
    max_attempts = max(2, min(12, int(os.environ.get("SUPABASE_MAX_ATTEMPTS", "3"))))
    timeout_sec = (
        float(request_timeout)
        if request_timeout is not None
        else float(os.environ.get("SUPABASE_HTTP_TIMEOUT", "45"))
    )

    for attempt in range(1, max_attempts + 1):
        response = requests.request(
            method, url, headers=headers, params=params, json=payload, timeout=timeout_sec
        )
        body_text = response.text or ""

        if response.status_code < 400:
            if not response.text:
                return []
            return response.json()

        body_lower = body_text.lower()
        is_schema_cache_retryable = response.status_code == 503 and (
            "pgrst002" in body_lower
            or "schema cache" in body_lower
        )
        # Plan Free / PGRST002: les longues boucles bloquent tout le dev. Re-essayer seulement si explicitement demande.
        retry_pgrst = os.environ.get("SUPABASE_PGRST002_RETRY", "0").lower() in ("1", "true", "yes")
        if is_schema_cache_retryable and attempt < max_attempts and retry_pgrst:
            sleep_s = min(45.0, 2.0 ** (attempt - 1))
            logger.warning(
                "Supabase schema cache indisponible (tentative %s/%s). Nouvelle tentative dans %.1fs...",
                attempt,
                max_attempts,
                sleep_s,
            )
            time.sleep(sleep_s)
            continue

        logger.error("Supabase request failed (%s): %s", response.status_code, body_text[:800])
        if is_schema_cache_retryable:
            raise HTTPException(
                status_code=503,
                detail=(
                    "Supabase reponn 503 (cache schema / PGRST002) apre plizye esè. "
                    "Atann 1 a 2 minit, verifye pwojè a an ligne, epi reessaeye. "
                    f"Fragment: {body_text[:600]}"
                ),
            )
        detail_msg = (body_text or response.reason or "Supabase request failed")[:4000]
        try:
            err_json = response.json()
            if isinstance(err_json, dict):
                msg = err_json.get("message") or err_json.get("error_description")
                hint = err_json.get("hint")
                code = err_json.get("code")
                if msg:
                    detail_msg = msg
                    if hint:
                        detail_msg = f"{detail_msg} ({hint})"
                    if code:
                        detail_msg = f"{detail_msg} [{code}]"
        except Exception:
            pass
        resp_status = response.status_code if 400 <= response.status_code < 600 else 500
        raise HTTPException(status_code=resp_status, detail=detail_msg)

    raise HTTPException(status_code=500, detail="Supabase request failed")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_agent_settings_from_request(data) -> Dict[str, Any]:
    return {
        "dry_run": data.dry_run,
        "max_profiles": data.max_profiles,
        "discover_youtube": data.discover_youtube,
        "discover_tiktok": data.discover_tiktok,
        "discover_instagram": data.discover_instagram,
        "discover_facebook": data.discover_facebook,
        "youtube_max_results": data.youtube_max_results,
    }


def merge_agent_settings(current: Dict[str, Any], update) -> Dict[str, Any]:
    merged = dict(current or {})
    if update.dry_run is not None:
        merged["dry_run"] = update.dry_run
    if update.max_profiles is not None:
        merged["max_profiles"] = update.max_profiles
    if update.discover_youtube is not None:
        merged["discover_youtube"] = update.discover_youtube
    if update.discover_tiktok is not None:
        merged["discover_tiktok"] = update.discover_tiktok
    if update.discover_instagram is not None:
        merged["discover_instagram"] = update.discover_instagram
    if update.discover_facebook is not None:
        merged["discover_facebook"] = update.discover_facebook
    if update.youtube_max_results is not None:
        merged["youtube_max_results"] = update.youtube_max_results
    return merged

# ─── Models ───────────────────────────────────────────────────────────────────

class ProfileInput(BaseModel):
    name: str
    bio: str
    platform: str  # facebook, tiktok, youtube
    followers: int
    content_example: str
    email: Optional[str] = None

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
    email: Optional[str] = None
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


def _stats_from_leads_rows(all_leads: List[Dict[str, Any]]) -> StatsResponse:
    total = len(all_leads)
    by_status: Dict[str, int] = {}
    by_platform: Dict[str, int] = {}
    total_score = 0
    high = medium = low = 0
    for lead in all_leads:
        s = lead.get("status", "new")
        by_status[s] = by_status.get(s, 0) + 1
        p = lead.get("platform", "unknown")
        by_platform[p] = by_platform.get(p, 0) + 1
        total_score += int(lead.get("score") or 0)
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
        avg_score=round(total_score / total, 1) if total > 0 else 0.0,
        high_potential=high,
        medium_potential=medium,
        low_potential=low,
    )


def _offline_append_agent_row(row: Dict[str, Any]) -> Dict[str, Any]:
    OFFLINE_AGENT_CONFIGS.insert(0, row)
    _persist_offline_agent_configs()
    return row


def _offline_remove_agent_by_id(agent_id: str) -> bool:
    aid = str(agent_id)
    before = len(OFFLINE_AGENT_CONFIGS)
    OFFLINE_AGENT_CONFIGS[:] = [c for c in OFFLINE_AGENT_CONFIGS if str(c.get("id")) != aid]
    if len(OFFLINE_AGENT_CONFIGS) < before:
        _persist_offline_agent_configs()
        return True
    return False


def _offline_append_lead_row(row: Dict[str, Any]) -> Dict[str, Any]:
    OFFLINE_LEADS.insert(0, row)
    return row


def _offline_insert_agent_run(row: Dict[str, Any]) -> str:
    rid = str(row.get("id") or uuid4())
    OFFLINE_AGENT_RUNS.insert(0, {**row, "id": rid})
    return rid


def _offline_merge_agent_run(run_id: str, updates: Dict[str, Any]) -> None:
    uid = str(run_id)
    for i, row in enumerate(OFFLINE_AGENT_RUNS):
        if str(row.get("id")) == uid:
            OFFLINE_AGENT_RUNS[i] = {**row, **updates}
            return
    OFFLINE_AGENT_RUNS.insert(0, {"id": uid, **updates})


def _get_agent_config(agent_id: str) -> Optional[Dict[str, Any]]:
    rows = _supabase_try_list(
        "GET",
        "/agent_configs",
        params={"id": f"eq.{agent_id}", "select": "*", "limit": "1"},
        request_timeout=_agent_supabase_timeout(),
    )
    if rows:
        return rows[0]
    for c in OFFLINE_AGENT_CONFIGS:
        if str(c.get("id")) == str(agent_id):
            return c
    return None


class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_hours: int


class AgentRunRequest(BaseModel):
    dry_run: bool = False
    max_profiles: int = 25
    discover_youtube: bool = True
    discover_tiktok: bool = True
    discover_instagram: bool = True
    discover_facebook: bool = True
    youtube_max_results: int = 20


class AgentRunResponse(BaseModel):
    run_id: str
    discovered: int
    scanned: int
    selected: int
    emailed: int
    dry_run: bool
    summary: str
    discovery_by_platform: Dict[str, int] = Field(default_factory=dict)


class AgentConfigCreateRequest(BaseModel):
    name: str
    function_type: str
    enabled: bool = True
    dry_run: bool = False
    max_profiles: int = 25
    discover_youtube: bool = True
    discover_tiktok: bool = True
    discover_instagram: bool = True
    discover_facebook: bool = True
    youtube_max_results: int = 20


class AgentConfigUpdateRequest(BaseModel):
    name: Optional[str] = None
    function_type: Optional[str] = None
    enabled: Optional[bool] = None
    dry_run: Optional[bool] = None
    max_profiles: Optional[int] = None
    discover_youtube: Optional[bool] = None
    discover_tiktok: Optional[bool] = None
    discover_instagram: Optional[bool] = None
    discover_facebook: Optional[bool] = None
    youtube_max_results: Optional[int] = None


class AgentConfigResponse(BaseModel):
    id: str
    name: str
    function_type: str
    enabled: bool
    settings: Dict[str, Any]
    created_by: Optional[str] = None
    created_at: str
    updated_at: Optional[str] = None


class AgentRunRecordResponse(BaseModel):
    id: str
    agent_id: Optional[str] = None
    agent_name: Optional[str] = None
    status: str
    run_type: str
    summary: Optional[str] = None
    details: Dict[str, Any] = {}
    triggered_by: Optional[str] = None
    started_at: str
    finished_at: Optional[str] = None


class AgentProfilePayload(BaseModel):
    """Pwofil agent (API) — alinye ak modèl Profile demann nan PRD."""

    model_config = ConfigDict(extra="ignore")

    id: Optional[str] = None
    username: str
    platform: str
    category: str = "Lòt"
    followers: int = 0
    bio: str = ""
    profile_url: str = ""
    email: Optional[str] = None
    creole_score: int = 0
    status: str = "found"
    created_at: Optional[str] = None


class AgentSearchRequest(BaseModel):
    category: str
    platforms: List[str]
    max_results: int = 20
    hashtags: Optional[List[str]] = None


class AgentSearchResponse(BaseModel):
    profiles: List[AgentProfilePayload]
    count: int
    # Si count=0 : pistes diagnostic (kle API, quota, etc.) — pa gen done sanspib
    search_hints: Optional[List[str]] = None


class AgentAnalyzeRequest(BaseModel):
    profiles: List[AgentProfilePayload]
    # 0 = pa filtre sou score kreyòl (retounen tout pwofil analize). Default 70 = ansyen konpòtman.
    min_creole_score: int = Field(default=70, ge=0, le=100)


class AgentAnalyzeResponse(BaseModel):
    profiles: List[AgentProfilePayload]
    count: int


class AgentSendEmailRequest(BaseModel):
    profile_id: str
    profile: AgentProfilePayload
    dry_run: bool = False


class AgentSendEmailResponse(BaseModel):
    ok: bool
    dry_run: bool
    message: str
    subject: Optional[str] = None
    body: Optional[str] = None
    resend_id: Optional[str] = None


class AgentStatusResponse(BaseModel):
    openai_configured: bool
    youtube_configured: bool
    apify_configured: bool
    resend_configured: bool
    smtp_configured: bool
    agent_model: str
    categories: List[str]
    message: str
    hashtag_suggestions: Dict[str, List[str]] = Field(default_factory=dict)

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

MESSAGE_SYSTEM_PROMPT = """Ou se yon espesyalis nan kominikasyon ak rekritman pou Konekte Group, yon platfom edikatif inovant ann Ayiti.

Objektif ou: ekri yon mesaj rekritman ki personalize, natirel, epi ki pa sanble spam.

RANFOSMAN LANG:
- Tout mesaj la DWE an KREYOL AYISYEN 100%.
- Pa itilize franse, pa itilize angle, pa melanje lang.
- Si w bezwen yon mo teknik, ekri li jan moun ann Ayiti itilize li, men toujou nan fraz kreyol.

Mesaj la DWE:
- Site yon eleman spesifik nan kontni moun nan
- Prezante Konekte Group tankou yon opotinite serye
- Rete cho, pwofesyonel, ak respekte moun nan
- Envite moun nan diskite san presyon
- Gen ant 3 ak 5 fraz maksimum

Reponn SELMAN ak teks mesaj la, san guillemets, san markdown, san lot fomataj."""


NON_KREYOL_MARKERS = {
    # French markers
    "bonjour", "merci", "recrutement", "plateforme", "educative", "discuter",
    "votre", "nous", "avec", "pour", "sans", "pression", "opportunite",
    # English markers
    "hello", "thanks", "opportunity", "platform", "educational", "recruitment",
    "discuss", "message", "professional", "warm", "content creator",
}


def is_message_mostly_kreyol(message: str) -> bool:
    """Heuristic guard: reject obvious French/English mixed messages."""
    text = (message or "").strip().lower()
    if not text:
        return False
    for marker in NON_KREYOL_MARKERS:
        if marker in text:
            return False
    return True


def compute_recruitment_fit_adjustments(profile: ProfileInput, analysis: dict) -> dict:
    """Adjust AI output with deterministic Konekte recruitment criteria."""
    domain = str(analysis.get("domain", "general")).strip().lower() or "general"
    raw_score = int(analysis.get("score", 50) or 50)
    score = max(0, min(100, raw_score))
    is_educator = bool(analysis.get("is_educator", False))
    platform = profile.platform.lower().strip()
    combined_text = f"{profile.bio} {profile.content_example}".lower()

    educational_keywords = [
        "prof",
        "enseign",
        "coach",
        "formateur",
        "formation",
        "cours",
        "tutoriel",
        "education",
        "pedagog",
        "apprendre",
        "eleve",
        "etudiant",
    ]
    has_educational_signals = any(k in combined_text for k in educational_keywords)

    if has_educational_signals:
        score += 10
    if domain in TARGET_DOMAINS:
        score += 10

    if profile.followers >= 100000:
        score += 20
    elif profile.followers >= 10000:
        score += 12
    elif profile.followers >= 1000:
        score += 6

    if platform == "youtube":
        score += 8
    elif platform == "tiktok":
        score += 4
    elif platform == "facebook":
        score += 2

    if not is_educator:
        score = min(score, 35)
    if not has_educational_signals:
        score -= 8

    score = max(0, min(100, score))
    if score >= 75:
        potential = "eleve"
    elif score >= 45:
        potential = "moyen"
    else:
        potential = "faible"

    base_reasoning = str(analysis.get("reasoning", "")).strip()
    adjustment_notes = []
    if domain in TARGET_DOMAINS:
        adjustment_notes.append("domaine prioritaire Konekte")
    if has_educational_signals:
        adjustment_notes.append("fort signal pedagogique")
    if profile.followers >= 10000:
        adjustment_notes.append("audience solide")

    reasoning_suffix = f" Ajustement Konekte: {', '.join(adjustment_notes)}." if adjustment_notes else ""
    return {
        "is_educator": is_educator,
        "domain": domain,
        "potential": potential,
        "score": score,
        "reasoning": (base_reasoning or "Analyse orientee recrutement formateur.") + reasoning_suffix,
    }


async def analyze_profile_with_ai(profile: ProfileInput) -> dict:
    """Use AI to analyze a profile and determine educator potential."""
    try:
        if not openai_client:
            raise RuntimeError("OPENAI_API_KEY is not set")

        completion = await openai_client.chat.completions.create(
            model=OPENAI_MODEL,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": ANALYSIS_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": f"""Analyse ce profil:
- Nom: {profile.name}
- Bio: {profile.bio}
- Plateforme: {profile.platform}
- Abonnes: {profile.followers}
- Exemple de contenu: {profile.content_example}""",
                },
            ],
        )

        response_text = completion.choices[0].message.content or "{}"
        cleaned = response_text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()

        analysis = json.loads(cleaned)
        return compute_recruitment_fit_adjustments(profile, analysis)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse AI analysis response: {e}")
        # Fallback analysis
        score = min(100, max(0, profile.followers // 1000 + 30))
        fallback = {
            "is_educator": True,
            "domain": "general",
            "potential": "moyen" if score > 40 else "faible",
            "score": score,
            "reasoning": "Analyse automatique basee sur les metriques du profil."
        }
        return compute_recruitment_fit_adjustments(profile, fallback)
    except Exception as e:
        logger.error(f"AI analysis error: {e}")
        score = min(100, max(0, profile.followers // 1000 + 30))
        fallback = {
            "is_educator": True,
            "domain": "general",
            "potential": "moyen" if score > 40 else "faible",
            "score": score,
            "reasoning": "Analyse automatique basee sur les metriques du profil."
        }
        return compute_recruitment_fit_adjustments(profile, fallback)


async def generate_recruitment_message(profile: ProfileInput, analysis: dict) -> str:
    """Use AI to generate a personalized recruitment message."""
    try:
        if not openai_client:
            raise RuntimeError("OPENAI_API_KEY is not set")

        user_prompt = f"""Genere un message de recrutement pour cette personne:
- Nom: {profile.name}
- Plateforme: {profile.platform}
- Domaine: {analysis.get('domain', 'education')}
- Contenu: {profile.content_example}
- Score: {analysis.get('score', 50)}/100

Rappel critique: mesaj final la dwe an kreyol ayisyen 100%."""

        for attempt in range(3):
            completion = await openai_client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": MESSAGE_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
            )
            candidate = (completion.choices[0].message.content or "").strip()
            if is_message_mostly_kreyol(candidate):
                return candidate

            logger.warning("Generated message rejected (non-kreyol) on attempt %s", attempt + 1)
            user_prompt = (
                f"{user_prompt}\n\nKoreksyon obligatwa: "
                "Re-ekri mesaj la an kreyol ayisyen selman, pa mete okenn mo franse oswa angle."
            )
    except Exception as e:
        logger.error(f"Message generation error: {e}")
    return f"Bonjou {profile.name}, mwen remake kontni ou ap fe sou {profile.platform} la epi li vreman enteresan. Konekte Group ap chache bon fomate tankou ou pou ede plis moun aprann. Eske ou ta disponib pou nou pale tou kout sou sa?"


def fetch_project_context() -> str:
    """Fetch and normalize project website context for outreach personalization."""
    try:
        resp = requests.get(PROJECT_URL, timeout=20)
        if resp.status_code >= 400:
            return "Konekte Group se yon platfom edikatif ki konekte aprenan ak bon fomate."
        text = re.sub(r"<[^>]+>", " ", resp.text)
        text = re.sub(r"\s+", " ", text).strip()
        return text[:2500] or "Konekte Group se yon platfom edikatif ki konekte aprenan ak bon fomate."
    except Exception:
        return "Konekte Group se yon platfom edikatif ki konekte aprenan ak bon fomate."


async def generate_outreach_email_kreyol(profile: dict, project_context: str) -> str:
    """Generate outbound outreach email in Haitian Creole only."""
    if not openai_client:
        return (
            f"Bonjou {profile.get('name', '')}, nou se ekip Konekte Group. "
            f"Nou remake travay ou ap fe a epi nou ta renmen envite ou vin kreye kont ou sou platfom nan: {PROJECT_SIGNUP_URL}. "
            "Si ou dakò, reponn imel sa a pou nou pale plis."
        )

    system_prompt = (
        "Ou se yon ajan rekritman pou Konekte Group. "
        "Ekri yon imèl kout an kreyòl ayisyen 100%, pwofesyonèl, cho, klè, san franse/angle. "
        "Objektif la se envite moun nan pou l kreye kont li sou platfòm la."
    )
    user_prompt = f"""
Enfòmasyon pwofil:
- Non: {profile.get('name', '')}
- Platfòm: {profile.get('platform', '')}
- Bio: {profile.get('bio', '')}
- Kontni: {profile.get('content_example', '')}
- Domèn: {profile.get('domain', '')}

Kontèks pwojè:
{project_context}

Kondisyon:
- 3-5 fraz
- Mete lyen enskripsyon sa a egzakteman: {PROJECT_SIGNUP_URL}
- Pa mete markdown, pa mete baliz
"""
    completion = await openai_client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
    )
    candidate = (completion.choices[0].message.content or "").strip()
    if not is_message_mostly_kreyol(candidate):
        return (
            f"Bonjou {profile.get('name', '')}, nou apresye kalite kontni ou yo. "
            f"Konekte Group ta renmen travay avè w kòm fomate sou platfòm la. "
            f"Tanpri kreye kont ou dirèkteman isit la: {PROJECT_SIGNUP_URL}. "
            "Si ou enterese, reponn mesaj sa a pou pwochen etap yo."
        )
    return candidate


def send_email_smtp(to_email: str, subject: str, body: str) -> bool:
    if not (SMTP_HOST and SMTP_USER and SMTP_PASSWORD):
        logger.warning("SMTP not configured: skipping email send.")
        return False
    try:
        msg = EmailMessage()
        msg["From"] = SMTP_FROM
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.set_content(body)
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=20) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
        return True
    except Exception as e:
        logger.error("SMTP send failed for %s: %s", to_email, e)
        return False


def extract_email_from_text(text: str) -> Optional[str]:
    if not text:
        return None
    match = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)
    return match.group(0) if match else None


def discover_youtube_channels(max_results: int) -> List[dict]:
    """Discover Haitian creator channels using YouTube Data API."""
    if not YOUTUBE_API_KEY:
        logger.warning("YOUTUBE_API_KEY is missing; skipping YouTube discovery.")
        return []

    discovered = []
    per_query = max(1, min(25, max_results // max(1, len(YOUTUBE_DISCOVERY_QUERIES))))
    for query in YOUTUBE_DISCOVERY_QUERIES:
        try:
            search_resp = requests.get(
                "https://www.googleapis.com/youtube/v3/search",
                params={
                    "part": "snippet",
                    "type": "channel",
                    "maxResults": per_query,
                    "q": query,
                    "key": YOUTUBE_API_KEY,
                    "regionCode": "HT",
                },
                timeout=20,
            )
            if search_resp.status_code >= 400:
                logger.warning("YouTube search failed for query '%s': %s", query, search_resp.text)
                continue

            items = search_resp.json().get("items", [])
            channel_ids = [i.get("id", {}).get("channelId") for i in items if i.get("id", {}).get("channelId")]
            if not channel_ids:
                continue

            channels_resp = requests.get(
                "https://www.googleapis.com/youtube/v3/channels",
                params={
                    "part": "snippet,statistics",
                    "id": ",".join(channel_ids),
                    "key": YOUTUBE_API_KEY,
                },
                timeout=20,
            )
            if channels_resp.status_code >= 400:
                logger.warning("YouTube channels lookup failed for query '%s': %s", query, channels_resp.text)
                continue

            for item in channels_resp.json().get("items", []):
                snippet = item.get("snippet", {})
                stats = item.get("statistics", {})
                description = snippet.get("description", "") or ""
                discovered.append(
                    {
                        "name": snippet.get("title", "Unknown Creator"),
                        "bio": description[:1000] or "Kreyatè kontni sou YouTube.",
                        "platform": "youtube",
                        "followers": int(stats.get("subscriberCount") or 0),
                        "content_example": (description[:200] or "Kontni YouTube pou kominote a."),
                        "email": extract_email_from_text(description),
                    }
                )
        except Exception as e:
            logger.warning("YouTube discovery error for query '%s': %s", query, e)

    # Deduplicate by normalized channel name
    unique = {}
    for profile in discovered:
        key = (profile.get("name") or "").strip().lower()
        if key and key not in unique:
            unique[key] = profile
    return list(unique.values())[:max_results]


async def upsert_discovered_profiles(profiles: List[dict], dry_run: bool) -> int:
    discovered_count = 0
    for profile in profiles:
        # Skip empty names
        if not (profile.get("name") or "").strip():
            continue

        if dry_run:
            discovered_count += 1
            continue

        existing = _supabase_try_list(
            "GET",
            "/leads",
            params={
                "select": "id",
                "platform": f"eq.{profile['platform']}",
                "name": f"eq.{profile['name']}",
                "limit": "1",
            },
        )
        if existing is None:
            if any(
                (l.get("name") or "").strip() == (profile.get("name") or "").strip()
                and str(l.get("platform") or "").lower() == str(profile.get("platform") or "").lower()
                for l in OFFLINE_LEADS
            ):
                continue
        elif existing:
            continue

        profile_input = ProfileInput(
            name=profile["name"],
            bio=profile.get("bio", ""),
            platform=profile["platform"],
            followers=profile.get("followers", 0),
            content_example=profile.get("content_example", ""),
            email=profile.get("email"),
        )
        analysis = await analyze_profile_with_ai(profile_input)
        lead_doc = {
            "name": profile_input.name,
            "bio": profile_input.bio,
            "platform": profile_input.platform,
            "followers": profile_input.followers,
            "content_example": profile_input.content_example,
            "email": profile_input.email,
            "is_educator": analysis.get("is_educator", False),
            "domain": analysis.get("domain", "general"),
            "potential": analysis.get("potential", "moyen"),
            "score": analysis.get("score", 50),
            "reasoning": analysis.get("reasoning", ""),
            "generated_message": "",
            "status": "new",
        }
        inserted = _supabase_try_call("POST", "/leads", payload=lead_doc)
        if not inserted:
            _offline_append_lead_row(
                {"id": str(uuid4()), "created_at": utc_now_iso(), **lead_doc}
            )
        discovered_count += 1

    return discovered_count


def _youtube_discovery_rows_to_lead_profiles(rows: List[Dict[str, Any]]) -> List[dict]:
    """Alinye sorti agent_recruiter (YouTube) ak `upsert_discovered_profiles`."""
    out: List[dict] = []
    for r in rows or []:
        bio = (r.get("bio") or "")[:2000]
        sn = (r.get("snippet") or "")[:500]
        combined = f"{bio}\n{sn}"
        name = (r.get("username") or "").strip() or "YouTube"
        out.append(
            {
                "name": name,
                "bio": bio,
                "platform": "youtube",
                "followers": int(r.get("followers") or 0),
                "content_example": (sn or bio[:200] or "Kontni YouTube.").strip(),
                "email": agent_rc.extract_email_from_text(combined),
            }
        )
    return out


def _agent_discovery_category() -> str:
    raw = (
        (os.environ.get("AGENT_DISCOVERY_CATEGORY") or os.environ.get("AGENT_YOUTUBE_CATEGORY") or "Edikasyon").strip()
        or "Edikasyon"
    )
    return agent_rc.normalize_category(raw)


def _social_discovery_row_to_lead(row: Dict[str, Any]) -> Optional[dict]:
    name = (row.get("username") or row.get("name") or "").strip()
    if not name:
        return None
    plat = str(row.get("platform", "tiktok")).lower().strip()
    bio = (row.get("bio") or "")[:2000]
    sn = (row.get("snippet") or "")[:500]
    combined = f"{bio}\n{sn}"
    ce = (sn or bio[:200] or f"Kontni {plat}.").strip()
    return {
        "name": name[:500],
        "bio": bio,
        "platform": plat,
        "followers": int(row.get("followers") or 0),
        "content_example": ce,
        "email": agent_rc.extract_email_from_text(combined) or row.get("email"),
    }


def _dedupe_lead_candidates(leads: List[dict]) -> List[dict]:
    seen: set = set()
    out: List[dict] = []
    for L in leads:
        plat = str(L.get("platform") or "").lower().strip()
        nm = (L.get("name") or "").strip().lower()
        if not nm:
            continue
        key = (plat, nm)
        if key in seen:
            continue
        seen.add(key)
        out.append(L)
    return out


async def execute_agent_cycle(payload: AgentRunRequest) -> Dict[str, Any]:
    """Execute one full discovery + outreach cycle and return metrics."""
    run_id = str(uuid4())
    project_context = fetch_project_context()
    discovered_count = 0
    cat = _agent_discovery_category()
    per = max(5, min(50, int(payload.youtube_max_results)))
    discovery_snap: Dict[str, int] = {}

    async def safe_disc(coro):
        try:
            return await coro
        except Exception as e:
            logger.warning("Agent discovery partial failure: %s", e)
            return None

    async def run_youtube_bundle():
        rows = await agent_rc.discover_youtube_agent_search_async(cat, per, None)
        leads = _youtube_discovery_rows_to_lead_profiles(rows)
        return "youtube", len(leads), leads

    async def run_tiktok_bundle():
        raw = await agent_rc.discover_tiktok_profiles(cat, per, None)
        leads = [x for x in (_social_discovery_row_to_lead(r) for r in (raw or [])) if x]
        return "tiktok", len(leads), leads

    async def run_instagram_bundle():
        raw = await agent_rc.discover_instagram_profiles(cat, per, None)
        leads = [x for x in (_social_discovery_row_to_lead(r) for r in (raw or [])) if x]
        return "instagram", len(leads), leads

    async def run_facebook_bundle():
        raw = await agent_rc.discover_facebook_profiles(cat, per, None)
        leads = [x for x in (_social_discovery_row_to_lead(r) for r in (raw or [])) if x]
        return "facebook", len(leads), leads

    tasks = []
    if payload.discover_youtube:
        tasks.append(safe_disc(run_youtube_bundle()))
    if payload.discover_tiktok:
        tasks.append(safe_disc(run_tiktok_bundle()))
    if payload.discover_instagram:
        tasks.append(safe_disc(run_instagram_bundle()))
    if payload.discover_facebook:
        tasks.append(safe_disc(run_facebook_bundle()))

    merged_leads: List[dict] = []
    for res in (await asyncio.gather(*tasks) if tasks else []):
        if not res:
            continue
        plat, nlead, leads = res
        discovery_snap[plat] = nlead
        merged_leads.extend(leads)

    if payload.discover_youtube and discovery_snap.get("youtube", -1) == 0:
        if not YOUTUBE_API_KEY:
            logger.warning(
                "Cycle agent: YOUTUBE_API_KEY manke — 0 pwofil YouTube. Mete kle nan .env epi aktive YouTube Data API v3."
            )
        else:
            logger.warning(
                "Cycle agent: YouTube retounen 0 kanaal (kategori=%s). Verifye quota / erè API nan konsol Google Cloud.",
                cat,
            )

    deduped = _dedupe_lead_candidates(merged_leads)
    discovered_count = await upsert_discovered_profiles(deduped, dry_run=payload.dry_run)

    params = {
        "select": "id,name,bio,platform,followers,content_example,email,domain,potential,score,status",
        "status": "eq.new",
        "order": "score.desc",
        "limit": str(max(1, min(payload.max_profiles, 100))),
    }
    lim = max(1, min(payload.max_profiles, 100))
    leads_rows = _supabase_try_list("GET", "/leads", params=params)
    if leads_rows is None:
        offline_new = [l for l in OFFLINE_LEADS if (l.get("status") or "new") == "new"]
        offline_new.sort(key=lambda x: int(x.get("score") or 0), reverse=True)
        leads = offline_new[:lim]
    else:
        leads = leads_rows
    scanned = len(leads)
    selected_rows = [
        lead for lead in leads
        if lead.get("potential") in ("eleve", "moyen") and (lead.get("email") or "").strip()
    ]

    emailed = 0
    if not payload.dry_run:
        for lead in selected_rows:
            email_body = await generate_outreach_email_kreyol(lead, project_context)
            sent = send_email_smtp(
                to_email=lead["email"].strip(),
                subject="Opotinite pou vin fomate sou Konekte Group",
                body=email_body,
            )
            if sent:
                emailed += 1
                patched = _supabase_try_call(
                    "PATCH",
                    "/leads",
                    params={"id": f"eq.{lead['id']}", "select": "*"},
                    payload={"status": "contacted"},
                )
                if patched is None:
                    for l in OFFLINE_LEADS:
                        if str(l.get("id")) == str(lead.get("id")):
                            l["status"] = "contacted"
                            break

    hints: List[str] = []
    if payload.discover_youtube:
        yt_candidates = discovery_snap.get("youtube", 0)
        if not YOUTUBE_API_KEY:
            hints.append(
                "YouTube: YOUTUBE_API_KEY manke nan backend/.env — mete la epi aktive YouTube Data API v3 (Google Cloud)"
            )
        elif yt_candidates == 0:
            hints.append(
                "YouTube: 0 kanaal jwenn — verifye quota / restriksyon kle la, oswa ogmante youtube_max_results nan konfig agent la"
            )
        elif discovered_count == 0 and not payload.dry_run and yt_candidates > 0:
            hints.append(
                f"YouTube: {yt_candidates} kanaal tente men 0 nouvo lead — yo ka deja nan tab Leads (menm non + platfòm)."
            )
    apify_key = bool(os.environ.get("APIFY_API_KEY", ""))
    any_social = payload.discover_tiktok or payload.discover_instagram or payload.discover_facebook
    if any_social and not apify_key:
        hints.append("Apify: APIFY_API_KEY manke — TikTok / Instagram / Facebook ap retounen 0 pwofil")
    if apify_key and any_social:
        apify_total = sum(discovery_snap.get(p, 0) for p in ("tiktok", "instagram", "facebook"))
        if apify_total == 0:
            hints.append(
                "Apify: 0 pwofil sosyal — verifye kredi Apify, timeout actor, oswa AGENT_DISCOVERY_CATEGORY nan .env"
            )
    if deduped and discovered_count == 0 and not payload.dry_run:
        hints.append(
            f"Dekouvèt: {len(deduped)} pwofil inik men 0 nouvo lead — yo ka deja nan tab Leads (menm non + platfòm)."
        )
    elif not deduped and (payload.discover_youtube or any_social):
        hints.append(
            "Dekouvèt: 0 pwofil nan tout sous aktif — verifye kle API, kategori (.env AGENT_DISCOVERY_CATEGORY), epi eseye ankò."
        )
    if scanned > 0 and not selected_rows:
        hints.append(
            "Seleksyon: sèlman leads ak imel + potential moyen/eleve — anpil chaèn YouTube pa gen imel nan bio"
        )
    if not payload.dry_run and scanned > 0 and not selected_rows:
        hints.append("SMTP: konfigire SMTP_* pou voye imel lè gen lead ki kalifye")
    hint_txt = (" " + " · ".join(hints)) if hints else ""
    snap_txt = ""
    if discovery_snap:
        snap_txt = " Kandida pa platfòm: " + ", ".join(f"{k}={v}" for k, v in sorted(discovery_snap.items()))

    summary = (
        f"Run {run_id}: {discovered_count} nouvo pwofil dekouvri, {scanned} pwofil analize, "
        f"{len(selected_rows)} pwofil seleksyone, {emailed if not payload.dry_run else 0} imel voye.{snap_txt}{hint_txt}"
    )
    return {
        "run_id": run_id,
        "discovered": discovered_count,
        "scanned": scanned,
        "selected": len(selected_rows),
        "emailed": 0 if payload.dry_run else emailed,
        "dry_run": payload.dry_run,
        "summary": summary,
        "discovery_by_platform": discovery_snap,
    }


# ─── Routes ───────────────────────────────────────────────────────────────────

@auth_router.post("/login", response_model=LoginResponse)
async def login(data: LoginRequest):
    ensure_supabase_auth_config()
    payload = {
        "email": data.email.strip().lower(),
        "password": data.password,
    }
    response = requests.post(
        f"{SUPABASE_AUTH_URL}/token?grant_type=password",
        headers=supabase_auth_headers(),
        json=payload,
        timeout=20,
    )
    if response.status_code >= 400:
        detail = "Email ou mot de passe invalide."
        try:
            error_json = response.json()
            detail = error_json.get("msg") or error_json.get("error_description") or detail
        except Exception:
            pass
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)

    auth_data = response.json()
    access_token = auth_data.get("access_token", "")
    expires_in_seconds = int(auth_data.get("expires_in") or 3600)
    if not access_token:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Login token missing.")

    expires_hours = max(1, (expires_in_seconds + 3599) // 3600)
    return LoginResponse(access_token=access_token, expires_in_hours=expires_hours)


@auth_router.get("/me")
async def me(current_user: str = Depends(require_auth)):
    return {"email": current_user}


@api_router.get("/")
async def root(current_user: str = Depends(require_auth)):
    return {"message": "Konekte AI Recruiter Agent API"}


@api_router.get("/health")
async def health_public():
    """Diagnostic leje: pa mande token."""
    return {
        "ok": True,
        "supabase_env_configured": bool(SUPABASE_URL and SUPABASE_KEY),
    }


@api_router.get("/health/supabase")
async def health_supabase(current_user: str = Depends(require_auth)):
    """
    Teste yon reket REST Supabase (leads, limit 1).
    Retounen 200 ak ok: false si erè (pou li fasil nan devtools).
    """
    try:
        t0 = time.time()
        rows = supabase_request("GET", "/leads", params={"select": "id", "limit": "1"})
        return {
            "ok": True,
            "sample_rows": len(rows or []),
            "latency_ms": round((time.time() - t0) * 1000, 1),
            "user": current_user,
        }
    except HTTPException as he:
        return {
            "ok": False,
            "http_status": he.status_code,
            "detail": he.detail,
            "hint": (
                "Si 503: souvan cache schema Supabase; tann e reessaeye. "
                "Si 42P01: execute backend/supabase_schema.sql. "
                "Verifye SUPABASE_URL ak SUPABASE_KEY (service_role si RLS)."
            ),
        }


@api_router.post("/analyze-profile", response_model=LeadResponse)
async def analyze_profile(profile: ProfileInput, current_user: str = Depends(require_auth)):
    """Analyze a profile using AI and save as a lead."""
    # AI Analysis
    analysis = await analyze_profile_with_ai(profile)

    # Generate recruitment message
    message = await generate_recruitment_message(profile, analysis)

    # Create lead record
    lead_doc = {
        "name": profile.name,
        "bio": profile.bio,
        "platform": profile.platform.lower(),
        "followers": profile.followers,
        "content_example": profile.content_example,
        "email": profile.email,
        "is_educator": analysis.get("is_educator", False),
        "domain": analysis.get("domain", "general"),
        "potential": analysis.get("potential", "moyen"),
        "score": analysis.get("score", 50),
        "reasoning": analysis.get("reasoning", ""),
        "generated_message": message,
        "status": "new"
    }

    inserted_rows = _supabase_try_call("POST", "/leads", payload=lead_doc)
    if inserted_rows:
        return LeadResponse(**inserted_rows[0])
    row = {
        "id": str(uuid4()),
        "created_at": utc_now_iso(),
        **lead_doc,
    }
    _offline_append_lead_row(row)
    return LeadResponse(**row)


@api_router.get("/leads", response_model=List[LeadResponse])
async def get_leads(
    status: Optional[str] = Query(None),
    platform: Optional[str] = Query(None),
    min_score: Optional[int] = Query(None),
    max_score: Optional[int] = Query(None),
    current_user: str = Depends(require_auth),
):
    """Get all leads with optional filtering."""
    params = {"select": "*", "order": "created_at.desc", "limit": "500"}
    if status:
        params["status"] = f"eq.{status}"
    if platform:
        params["platform"] = f"eq.{platform.lower()}"
    if min_score is not None and max_score is not None:
        params["and"] = f"(score.gte.{min_score},score.lte.{max_score})"
    elif min_score is not None:
        params["score"] = f"gte.{min_score}"
    elif max_score is not None:
        params["score"] = f"lte.{max_score}"

    rows = _supabase_try_list("GET", "/leads", params=params)
    if rows is None:
        return _filter_leads_local(OFFLINE_LEADS, status, platform, min_score, max_score)
    return rows


@api_router.patch("/leads/{lead_id}/status")
async def update_lead_status(lead_id: str, update: LeadStatusUpdate, current_user: str = Depends(require_auth)):
    """Update the status of a lead."""
    if update.status not in ["new", "contacted", "replied"]:
        raise HTTPException(status_code=400, detail="Status must be: new, contacted, or replied")

    result = supabase_request(
        "PATCH",
        "/leads",
        params={"id": f"eq.{lead_id}", "select": "*"},
        payload={"status": update.status},
    )
    if not result:
        raise HTTPException(status_code=404, detail="Lead not found")

    return {"message": "Status updated", "id": lead_id, "status": update.status}


@api_router.delete("/leads/{lead_id}")
async def delete_lead(lead_id: str, current_user: str = Depends(require_auth)):
    """Delete a lead."""
    result = supabase_request("DELETE", "/leads", params={"id": f"eq.{lead_id}", "select": "*"})
    if not result:
        raise HTTPException(status_code=404, detail="Lead not found")
    return {"message": "Lead deleted", "id": lead_id}


@api_router.get("/leads/stats", response_model=StatsResponse)
async def get_leads_stats(current_user: str = Depends(require_auth)):
    """Get dashboard statistics."""
    all_leads = _supabase_try_list(
        "GET",
        "/leads",
        params={"select": "status,platform,score,potential", "limit": "1000"},
    )
    if all_leads is None:
        return _stats_from_leads_rows(list(OFFLINE_LEADS))
    return _stats_from_leads_rows(all_leads)


@api_router.post("/leads/{lead_id}/regenerate-message")
async def regenerate_message(lead_id: str, current_user: str = Depends(require_auth)):
    """Regenerate the recruitment message for an existing lead."""
    lead_rows = supabase_request(
        "GET",
        "/leads",
        params={"id": f"eq.{lead_id}", "select": "*", "limit": "1"},
    )
    if not lead_rows:
        raise HTTPException(status_code=404, detail="Lead not found")
    lead = lead_rows[0]

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

    supabase_request(
        "PATCH",
        "/leads",
        params={"id": f"eq.{lead_id}", "select": "*"},
        payload={"generated_message": new_message},
    )

    return {"message": new_message, "id": lead_id}


@api_router.get("/agents", response_model=List[AgentConfigResponse])
async def list_agents(current_user: str = Depends(require_auth)):
    rows = _supabase_try_list(
        "GET",
        "/agent_configs",
        params={"select": "*", "order": "created_at.desc", "limit": "200"},
        request_timeout=_agent_supabase_timeout(),
    )
    if rows is not None and rows:
        _prune_offline_agents_that_exist_remotely(rows)
    return _merge_remote_and_offline_agent_configs(rows)


@api_router.post("/agents", response_model=AgentConfigResponse)
async def create_agent(
    data: AgentConfigCreateRequest,
    background_tasks: BackgroundTasks,
    current_user: str = Depends(require_auth),
):
    settings = build_agent_settings_from_request(data)
    payload = {
        "name": data.name.strip(),
        "function_type": data.function_type.strip(),
        "enabled": data.enabled,
        "settings": settings,
        "created_by": current_user,
        "created_at": utc_now_iso(),
        "updated_at": utc_now_iso(),
    }
    if AGENT_CREATE_OFFLINE_FIRST:
        aid = str(uuid4())
        row = {"id": aid, **payload}
        saved = _offline_append_agent_row(row)
        if SUPABASE_URL and SUPABASE_KEY:
            background_tasks.add_task(_sync_agent_create_to_supabase, aid, dict(payload))
        return saved
    rows = _supabase_try_call(
        "POST", "/agent_configs", payload=payload, request_timeout=_agent_supabase_timeout()
    )
    if rows:
        return rows[0]
    row = {"id": str(uuid4()), **payload}
    return _offline_append_agent_row(row)


@api_router.patch("/agents/{agent_id}", response_model=AgentConfigResponse)
async def update_agent(agent_id: str, data: AgentConfigUpdateRequest, current_user: str = Depends(require_auth)):
    existing = _get_agent_config(agent_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Agent not found.")

    merged_settings = merge_agent_settings(existing.get("settings", {}) or {}, data)
    update_payload = {"settings": merged_settings, "updated_at": utc_now_iso()}
    if data.name is not None:
        update_payload["name"] = data.name.strip()
    if data.function_type is not None:
        update_payload["function_type"] = data.function_type.strip()
    if data.enabled is not None:
        update_payload["enabled"] = data.enabled

    rows = _supabase_try_call(
        "PATCH",
        "/agent_configs",
        params={"id": f"eq.{agent_id}", "select": "*"},
        payload=update_payload,
        request_timeout=_agent_supabase_timeout(),
    )
    if rows:
        _offline_remove_agent_by_id(agent_id)
        return rows[0]
    for i, c in enumerate(OFFLINE_AGENT_CONFIGS):
        if str(c.get("id")) == str(agent_id):
            updated = {**c, **update_payload}
            OFFLINE_AGENT_CONFIGS[i] = updated
            _persist_offline_agent_configs()
            return updated
    raise HTTPException(status_code=500, detail="Failed to update agent.")


@api_router.delete("/agents/{agent_id}")
async def delete_agent(agent_id: str, current_user: str = Depends(require_auth)):
    """Siprime agent: Supabase si posib, epi fichye offline."""
    cfg = _get_agent_config(agent_id)
    if not cfg:
        raise HTTPException(status_code=404, detail="Agent not found.")
    had_offline = _offline_remove_agent_by_id(agent_id)
    if SUPABASE_URL and SUPABASE_KEY:
        try:
            supabase_request(
                "DELETE",
                "/agent_configs",
                params={"id": f"eq.{agent_id}", "select": "*"},
                request_timeout=_agent_supabase_timeout(),
            )
        except HTTPException as e:
            if _is_transient_supabase_failure(e) or e.status_code >= 500:
                raise
            if not had_offline:
                raise
            logger.info("DELETE agent Supabase (optional, agent te offline): %s", e.detail)
    return {"message": "Agent deleted.", "id": agent_id}


@api_router.get("/agents/runs", response_model=List[AgentRunRecordResponse])
async def list_agent_runs(current_user: str = Depends(require_auth)):
    rows = _supabase_try_list(
        "GET",
        "/agent_runs",
        params={"select": "*", "order": "started_at.desc", "limit": "300"},
        request_timeout=_agent_supabase_timeout(),
    )
    source = rows if rows is not None else OFFLINE_AGENT_RUNS
    normalized = []
    for row in source:
        normalized.append({**row, "details": row.get("details") or {}})
    return normalized


@api_router.post("/agents/{agent_id}/run", response_model=AgentRunResponse)
async def run_named_agent(agent_id: str, current_user: str = Depends(require_auth)):
    config = _get_agent_config(agent_id)
    if not config:
        raise HTTPException(status_code=404, detail="Agent not found.")
    if not config.get("enabled", True):
        raise HTTPException(status_code=400, detail="Agent is disabled.")

    settings = config.get("settings") or {}
    payload = AgentRunRequest(
        dry_run=bool(settings.get("dry_run", False)),
        max_profiles=int(settings.get("max_profiles", 25)),
        discover_youtube=bool(settings.get("discover_youtube", True)),
        discover_tiktok=bool(settings.get("discover_tiktok", True)),
        discover_instagram=bool(settings.get("discover_instagram", True)),
        discover_facebook=bool(settings.get("discover_facebook", True)),
        youtube_max_results=int(settings.get("youtube_max_results", 20)),
    )

    run_row = {
        "agent_id": agent_id,
        "agent_name": config.get("name", ""),
        "status": "running",
        "run_type": config.get("function_type", "recruitment"),
        "summary": "Agent run started",
        "details": {},
        "triggered_by": current_user,
        "started_at": utc_now_iso(),
    }
    run_record_rows = _supabase_try_call(
        "POST", "/agent_runs", payload=run_row, request_timeout=_agent_supabase_timeout()
    )
    if run_record_rows:
        run_record_id = run_record_rows[0].get("id")
    else:
        run_record_id = _offline_insert_agent_run({**run_row, "id": str(uuid4())})

    def patch_run_record(updates: Dict[str, Any]) -> None:
        patched = _supabase_try_call(
            "PATCH",
            "/agent_runs",
            params={"id": f"eq.{run_record_id}", "select": "*"},
            payload=updates,
            request_timeout=_agent_supabase_timeout(),
        )
        if patched is None:
            _offline_merge_agent_run(str(run_record_id), updates)

    try:
        result = await execute_agent_cycle(payload)
        patch_run_record(
            {
                "status": "completed",
                "summary": result["summary"],
                "details": result,
                "finished_at": utc_now_iso(),
            }
        )
        return AgentRunResponse(**result)
    except Exception as e:
        patch_run_record(
            {
                "status": "failed",
                "summary": f"Agent failed: {e}",
                "details": {"error": str(e)},
                "finished_at": utc_now_iso(),
            }
        )
        raise


@api_router.post("/agent/run", response_model=AgentRunResponse)
async def run_agent(payload: AgentRunRequest, current_user: str = Depends(require_auth)):
    """Run default agent cycle directly from dashboard quick action."""
    result = await execute_agent_cycle(payload)
    return AgentRunResponse(**result)


@api_router.get("/agent/status", response_model=AgentStatusResponse)
async def agent_status(current_user: str = Depends(require_auth)):
    """Estati konfigirasyon agent rekritman kreyòl."""
    return AgentStatusResponse(
        openai_configured=bool(OPENAI_API_KEY),
        youtube_configured=bool(YOUTUBE_API_KEY),
        apify_configured=bool(os.environ.get("APIFY_API_KEY", "")),
        resend_configured=bool(os.environ.get("RESEND_API_KEY", "")),
        smtp_configured=bool(SMTP_HOST and SMTP_USER and SMTP_PASSWORD),
        agent_model=AGENT_LLM_MODEL,
        categories=list(agent_rc.CATEGORY_HASHTAGS.keys()),
        message="API pare pou rechèch, analiz, epi voye imèl (si kle yo ranpli).",
        hashtag_suggestions={k: list(v) for k, v in agent_rc.HASHTAGS_PAR_CATEGORIE.items()},
    )


_PLACEHOLDER_AGENT_USERNAMES = frozenset({"test_ayisyen_biznis", "test_pipeline_ok"})


def _agent_raw_row_is_placeholder(row: Dict[str, Any]) -> bool:
    """Retire ansyen pwofil dev / fallback — sèlman kandida reyèl."""
    u = (row.get("username") or "").strip().lower()
    if u in _PLACEHOLDER_AGENT_USERNAMES:
        return True
    url = (row.get("profile_url") or "").strip().lower().rstrip("/")
    if url.endswith("/@test") or url.endswith("tiktok.com/@test"):
        return True
    return False


@api_router.post("/agent/search", response_model=AgentSearchResponse)
async def agent_search(payload: AgentSearchRequest, current_user: str = Depends(require_auth)):
    """Dekouvèt pwofil sou TikTok, YouTube, Facebook, Instagram selon kategori ak hashtags kreyòl."""
    cat = agent_rc.normalize_category(payload.category)
    max_r = max(1, min(100, int(payload.max_results or 20)))
    plats = [p.lower().strip() for p in (payload.platforms or []) if p.strip()]
    if not plats:
        raise HTTPException(status_code=400, detail="Chwazi omwen yon platfòm.")

    custom_ht: Optional[List[str]] = None
    if payload.hashtags:
        custom_ht = agent_rc.normalize_custom_hashtags(payload.hashtags)
        if not custom_ht:
            custom_ht = None

    # Plis kandida pa sous anvan dedup username (anpil platfòm = mwens pa youn)
    per = max(8, max(1, max_r // max(1, len(plats))))
    raw_profiles: List[Dict[str, Any]] = []

    async def safe(coro):
        try:
            return await coro
        except Exception as e:
            logger.warning("Agent search partial failure: %s", e)
            return []

    async def youtube_profiles_safe() -> List[Dict[str, Any]]:
        if "youtube" not in plats:
            return []
        try:
            rows = await agent_rc.discover_youtube_agent_search_async(cat, per, custom_ht)
            out = []
            for row in rows or []:
                uname = (row.get("username") or row.get("name") or "YouTube").strip() or "YouTube"
                out.append(
                    {
                        "username": uname,
                        "platform": "youtube",
                        "followers": row.get("followers", 0),
                        "bio": row.get("bio", ""),
                        "profile_url": row.get("profile_url", ""),
                        "snippet": row.get("snippet", ""),
                    }
                )
            return out
        except Exception as e:
            logger.warning("YouTube discovery in agent_search: %s", e)
            return []

    # TikTok + YouTube (ak lòt platfòm si chwazi) — asyncio.gather pou paralèl
    tasks = []
    if "tiktok" in plats:
        tasks.append(safe(agent_rc.discover_tiktok_profiles(cat, per, custom_ht)))
    if "youtube" in plats:
        tasks.append(safe(youtube_profiles_safe()))
    if "instagram" in plats:
        tasks.append(safe(agent_rc.discover_instagram_profiles(cat, per, custom_ht)))
    if "facebook" in plats:
        tasks.append(safe(agent_rc.discover_facebook_profiles(cat, per, custom_ht)))
    if tasks:
        parts = await asyncio.gather(*tasks)
        for part in parts:
            raw_profiles.extend(part or [])

    # Dedupe pa username sèlman (tout platfòm), limite max_r
    seen: set = set()
    merged: List[Dict[str, Any]] = []
    for row in raw_profiles:
        if _agent_raw_row_is_placeholder(row):
            continue
        name_key = (row.get("username") or "").strip().lower()
        if not name_key:
            continue
        if name_key in seen:
            continue
        seen.add(name_key)
        merged.append(row)
        if len(merged) >= max_r:
            break

    out: List[AgentProfilePayload] = []
    for row in merged[:max_r]:
        bio = (row.get("bio") or "").strip()
        sn = (row.get("snippet") or "").strip()
        if sn:
            bio = (bio + "\n\n" + sn).strip()[:8000]
        email = agent_rc.extract_email_from_text(bio) or row.get("email")
        out.append(
            AgentProfilePayload(
                id=str(uuid4()),
                username=(row.get("username") or "unknown")[:500],
                platform=str(row.get("platform", "tiktok")).lower(),
                category=cat,
                followers=int(row.get("followers") or 0),
                bio=bio,
                profile_url=(row.get("profile_url") or "")[:2000],
                email=email,
                creole_score=0,
                status="found",
                created_at=utc_now_iso(),
            )
        )

    hints: Optional[List[str]] = None
    if len(out) == 0:
        hints = []
        apify_ok = bool(os.environ.get("APIFY_API_KEY", "").strip())
        yt_ok = bool((YOUTUBE_API_KEY or "").strip())
        if "tiktok" in plats and not apify_ok:
            hints.append(
                "TikTok : ajoutez APIFY_API_KEY dans backend/.env ou .env à la racine, puis redémarrez uvicorn."
            )
        if "youtube" in plats and not yt_ok:
            hints.append(
                "YouTube : ajoutez YOUTUBE_API_KEY (projet Google Cloud avec API YouTube Data v3 activée)."
            )
        if ("instagram" in plats or "facebook" in plats) and not apify_ok:
            hints.append("Instagram / Facebook : la même variable APIFY_API_KEY est requise (acteurs Apify).")
        if not hints:
            hints.append(
                "Clés détectées mais 0 profil : quotas ou limites Apify, hashtags trop étroits, "
                "ou format de données TikTok — regardez la console uvicorn (lignes [apify], [tiktok], [youtube]). "
                "Testez d’abord une seule plateforme (ex. YouTube seul) avec une catégorie large."
            )
    return AgentSearchResponse(profiles=out, count=len(out), search_hints=hints)


@api_router.post("/agent/analyze", response_model=AgentAnalyzeResponse)
async def agent_analyze(payload: AgentAnalyzeRequest, current_user: str = Depends(require_auth)):
    """Analiz kreyòl ak OpenAI; filtre sou min_creole_score (default 70). Mete min_creole_score=0 pou tout retounen."""
    analyze_sem = asyncio.Semaphore(6)

    async def score_one(p: AgentProfilePayload):
        async with analyze_sem:
            pd = {
                "username": p.username,
                "platform": p.platform,
                "bio": p.bio or "",
                "snippet": "",
                "category": p.category,
            }
            hint = await agent_rc.analyze_creole_score(openai_client, AGENT_LLM_MODEL, pd)
            return p, hint

    scored_pairs = await asyncio.gather(*[score_one(p) for p in payload.profiles])

    min_sc = max(0, min(100, int(payload.min_creole_score)))
    results: List[AgentProfilePayload] = []
    for p, hint in scored_pairs:
        score = int(hint.get("creole_score") or 0)
        if min_sc > 0 and score <= min_sc:
            continue

        potential = "eleve" if score >= 85 else "moyen"
        reasoning = (hint.get("reasoning") or "").strip()
        reasoning = f"[Kreyòl {score}/100] {reasoning}"[:8000]

        content_example = (p.profile_url or "").strip()
        if p.bio:
            content_example = (content_example + "\n\n" + p.bio[:3000]).strip() if content_example else p.bio[:4000]

        lead_doc = {
            "name": p.username[:500],
            "bio": (p.bio or "")[:8000],
            "platform": p.platform.lower(),
            "followers": int(p.followers or 0),
            "content_example": content_example[:8000] or "—",
            "email": (p.email or "").strip() or None,
            "is_educator": True,
            "domain": agent_rc.normalize_category(p.category),
            "potential": potential,
            "score": score,
            "reasoning": reasoning,
            "generated_message": "",
            "status": "new",
        }

        new_id: Optional[str] = None
        try:
            if SUPABASE_URL and SUPABASE_KEY:
                existing = supabase_request(
                    "GET",
                    "/leads",
                    params={
                        "select": "id,score",
                        "platform": f"eq.{lead_doc['platform']}",
                        "name": f"eq.{lead_doc['name']}",
                        "limit": "1",
                    },
                )
                if existing:
                    new_id = existing[0]["id"]
                    supabase_request(
                        "PATCH",
                        "/leads",
                        params={"id": f"eq.{new_id}", "select": "*"},
                        payload={
                            "score": score,
                            "reasoning": reasoning,
                            "potential": potential,
                            "bio": lead_doc["bio"],
                            "followers": lead_doc["followers"],
                            "content_example": lead_doc["content_example"],
                            "email": lead_doc["email"] or existing[0].get("email"),
                        },
                    )
                else:
                    inserted = supabase_request("POST", "/leads", payload=lead_doc)
                    new_id = inserted[0]["id"] if inserted else None
        except Exception as e:
            logger.warning("Lead save skipped/failed: %s", e)
            new_id = p.id or str(uuid4())

        results.append(
            AgentProfilePayload(
                id=new_id or str(uuid4()),
                username=p.username,
                platform=p.platform,
                category=agent_rc.normalize_category(p.category),
                followers=int(p.followers or 0),
                bio=p.bio,
                profile_url=p.profile_url,
                email=p.email,
                creole_score=score,
                status="analyzed",
                created_at=p.created_at or utc_now_iso(),
            )
        )

    return AgentAnalyzeResponse(profiles=results, count=len(results))


@api_router.post("/agent/send-email", response_model=AgentSendEmailResponse)
async def agent_send_email(payload: AgentSendEmailRequest, current_user: str = Depends(require_auth)):
    """Jenere imèl an kreyòl epi voye atravè Resend (contact@konektegroup.com). dry_run=true pou previzyalizasyon."""
    prof = payload.profile
    to_email = (prof.email or "").strip()
    if not to_email:
        raise HTTPException(status_code=400, detail="Pa gen adrès imèl sou pwofil la.")

    draft = await agent_rc.generate_recruitment_email_openai(openai_client, AGENT_LLM_MODEL, prof.model_dump())
    subject = draft.get("subject") or "KonekteGroup"
    body = draft.get("body") or ""

    if payload.dry_run:
        return AgentSendEmailResponse(
            ok=True,
            dry_run=True,
            message="Previzyalizasyon imèl pare.",
            subject=subject,
            body=body,
            resend_id=None,
        )

    ok, info = agent_rc.send_email_resend(to_email, subject, body)
    if not ok:
        raise HTTPException(status_code=502, detail=f"Resend echwe: {info}")

    # Mete ajou lead si id Supabase
    try:
        if SUPABASE_URL and SUPABASE_KEY and payload.profile_id:
            supabase_request(
                "PATCH",
                "/leads",
                params={"id": f"eq.{payload.profile_id}", "select": "*"},
                payload={
                    "status": "contacted",
                    "generated_message": body,
                    "email": to_email,
                },
            )
    except Exception as e:
        logger.warning("Could not update lead after email: %s", e)

    return AgentSendEmailResponse(
        ok=True,
        dry_run=False,
        message="Imèl voye ak siksè.",
        subject=subject,
        body=body,
        resend_id=str(info)[:120],
    )


# Include router and middleware
app.include_router(auth_router)
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "https://agentai.konektegroup.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve frontend from FastAPI (single unified app/runtime)
if FRONTEND_BUILD_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_BUILD_DIR / "static")), name="static")

    @app.get("/", include_in_schema=False)
    async def serve_frontend_root():
        return FileResponse(str(FRONTEND_BUILD_DIR / "index.html"))

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_frontend_app(full_path: str):
        if full_path.startswith("api"):
            raise HTTPException(status_code=404, detail="API route not found")
        candidate = FRONTEND_BUILD_DIR / full_path
        if candidate.exists() and candidate.is_file():
            return FileResponse(str(candidate))
        return FileResponse(str(FRONTEND_BUILD_DIR / "index.html"))
