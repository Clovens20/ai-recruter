"""
Agent recrutement KonekteGroup : dekouvèt pwofil, analiz kreyòl, voye imèl (Resend).
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import requests

logger = logging.getLogger(__name__)

APIFY_TOKEN = os.environ.get("APIFY_API_KEY", "")
# Tan maks Apify `call(wait_secs=...)` — pi ba = pi vit, men riske timeout si actor a lan
APIFY_WAIT_SECS = max(25, min(180, int(os.environ.get("APIFY_WAIT_SECS", "70"))))
# Mwen hashtags = actor TikTok fini pi vit
APIFY_TIKTOK_HASHTAG_COUNT = max(1, min(8, int(os.environ.get("APIFY_TIKTOK_HASHTAG_COUNT", "2"))))
APIFY_TIKTOK_RESULTS_CAP = max(3, min(40, int(os.environ.get("APIFY_TIKTOK_RESULTS_CAP", "12"))))
YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY", "")
# YouTube: mwens requetes si fast (default)
AGENT_YOUTUBE_FAST = os.environ.get("AGENT_YOUTUBE_FAST", "1").lower() in ("1", "true", "yes")
RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
RESEND_FROM = os.environ.get("RESEND_FROM", "contact@konektegroup.com")
KONEKTE_URL = os.environ.get("KONEKTEGROUP_URL", "https://konektegroup.com")

# Actors Apify (peut override pa .env)
APIFY_TIKTOK_ACTOR = os.environ.get("APIFY_TIKTOK_ACTOR", "clockworks/tiktok-scraper")
APIFY_INSTAGRAM_ACTOR = os.environ.get("APIFY_INSTAGRAM_ACTOR", "apify/instagram-hashtag-scraper")
APIFY_FACEBOOK_ACTOR = os.environ.get("APIFY_FACEBOOK_ACTOR", "apify/facebook-search-scraper")

CATEGORY_HASHTAGS: Dict[str, List[str]] = {
    "Teknoloji": ["teknoloji", "teknolojikreyol", "informatik", "pwogramasyon"],
    "Marketing Digital": ["maketing", "rezososiyal", "biznisonline", "marketingkreyol"],
    "AI": ["entelijanatifisyel", "AI", "chatgpt", "teknoloji"],
    "Finance": ["finans", "lajan", "envesdisman", "kryptokreyol"],
    "Biznis": ["biznis", "antreprenè", "komès", "biznishan"],
    "Kreatif": ["kreyatif", "atis", "design", "foto"],
    "Sante": ["sante", "lasante", "medisin", "byennet"],
    "Lang": ["langkreyol", "angle", "espanyol", "fransè"],
    "Mizik": ["mizik", "chante", "danse", "mizikkreyol"],
    "Devlopman Pèsonèl": ["siksè", "motivasyon", "devlopman", "lidèchip"],
    "Edikasyon": ["edikasyon", "lekòl", "etid", "aprann"],
    "Travay Atizana": ["atizana", "metye", "travay", "crafts"],
    "Lòt": ["kreyol", "ayiti", "formasyon", "kreyòl"],
}

# Requête YouTube (Data API v3) — mo kle + kategori
YOUTUBE_EXTRA_TERMS = [
    "kreyol ayisyen",
    "kreyòl",
    "haitian creole",
    "formateur haiti",
    "Ayiti",
]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_category(category: str) -> str:
    c = (category or "").strip()
    if c in CATEGORY_HASHTAGS:
        return c
    for k in CATEGORY_HASHTAGS:
        if k.lower() == c.lower():
            return k
    return "Lòt"


def hashtags_for_category(category: str) -> List[str]:
    return CATEGORY_HASHTAGS.get(normalize_category(category), CATEGORY_HASHTAGS["Lòt"])


def youtube_queries_for_category(category: str, max_queries: int = 4) -> List[str]:
    tags = hashtags_for_category(category)[:3]
    queries: List[str] = []
    for t in tags:
        queries.append(f"{t} {' '.join(YOUTUBE_EXTRA_TERMS[:2])}")
    queries.append(f"{normalize_category(category)} {' '.join(YOUTUBE_EXTRA_TERMS)}")
    return queries[:max_queries]


def _apify_run_sync(actor_id: str, run_input: Dict[str, Any], timeout_secs: Optional[int] = None) -> List[Dict[str, Any]]:
    if timeout_secs is None:
        timeout_secs = APIFY_WAIT_SECS
    if not APIFY_TOKEN:
        logger.warning("APIFY_API_KEY manke; Apify pa disponib.")
        return []
    try:
        from apify_client import ApifyClient

        client = ApifyClient(APIFY_TOKEN)
        run = client.actor(actor_id).call(run_input=run_input, wait_secs=timeout_secs)
        did = run.get("defaultDatasetId")
        if not did:
            return []
        out: List[Dict[str, Any]] = []
        for item in client.dataset(did).iterate_items():
            out.append(item)
        return out
    except Exception as e:
        logger.exception("Apify actor %s echwe: %s", actor_id, e)
        return []


async def apify_run(
    actor_id: str, run_input: Dict[str, Any], timeout_secs: Optional[int] = None
) -> List[Dict[str, Any]]:
    return await asyncio.to_thread(_apify_run_sync, actor_id, run_input, timeout_secs)


async def discover_tiktok_profiles(category: str, max_results: int) -> List[Dict[str, Any]]:
    hashtags_all = hashtags_for_category(category)
    hashtags = hashtags_all[:APIFY_TIKTOK_HASHTAG_COUNT]
    results_cap = min(max_results, APIFY_TIKTOK_RESULTS_CAP, 30)
    items = await apify_run(
        APIFY_TIKTOK_ACTOR,
        {
            "hashtags": hashtags,
            "resultsPerPage": results_cap,
            "shouldDownloadVideos": False,
            "shouldDownloadCovers": False,
        },
    )
    profiles: List[Dict[str, Any]] = []
    seen: set = set()
    for item in items:
        author = item.get("authorMeta") or item.get("author") or {}
        name = (author.get("name") or author.get("uniqueId") or "").strip()
        if not name:
            continue
        key = ("tiktok", name.lower())
        if key in seen:
            continue
        seen.add(key)
        uid = author.get("uniqueId") or name
        profiles.append(
            {
                "username": name,
                "platform": "tiktok",
                "followers": int(author.get("fans") or author.get("followerCount") or 0),
                "bio": (author.get("signature") or author.get("bio") or "")[:2000],
                "profile_url": f"https://www.tiktok.com/@{uid}" if uid else "",
                "snippet": (item.get("text") or item.get("desc") or "")[:500],
            }
        )
        if len(profiles) >= max_results:
            break
    return profiles


async def discover_instagram_profiles(category: str, max_results: int) -> List[Dict[str, Any]]:
    hashtags = [h.lstrip("#") for h in hashtags_for_category(category)[:4]]
    items = await apify_run(
        APIFY_INSTAGRAM_ACTOR,
        {
            "hashtags": hashtags,
            "resultsLimit": min(max_results, 12),
            "resultsType": "posts",
        },
    )
    profiles: List[Dict[str, Any]] = []
    seen: set = set()
    for item in items:
        owner = (item.get("ownerUsername") or item.get("username") or "").strip()
        if not owner:
            continue
        key = ("instagram", owner.lower())
        if key in seen:
            continue
        seen.add(key)
        profiles.append(
            {
                "username": owner,
                "platform": "instagram",
                "followers": int(item.get("followersCount") or item.get("ownerFollowersCount") or 0),
                "bio": (item.get("biography") or item.get("caption") or "")[:2000],
                "profile_url": f"https://www.instagram.com/{owner}/",
                "snippet": (item.get("caption") or "")[:500],
            }
        )
        if len(profiles) >= max_results:
            break
    return profiles


async def discover_facebook_profiles(category: str, max_results: int) -> List[Dict[str, Any]]:
    tags = hashtags_for_category(category)[:2]
    queries = [f"{t} kreyol ayiti" for t in tags]
    items = await apify_run(
        APIFY_FACEBOOK_ACTOR,
        {"searchQueries": queries, "maxResults": min(max_results, 10)},
    )
    profiles: List[Dict[str, Any]] = []
    seen: set = set()
    for item in items:
        name = (item.get("title") or item.get("name") or item.get("pageName") or "").strip()
        link = (item.get("url") or item.get("pageUrl") or item.get("facebookUrl") or "").strip()
        if not name and link:
            name = link.rstrip("/").split("/")[-1] or "facebook"
        if not name:
            continue
        key = ("facebook", name.lower())
        if key in seen:
            continue
        seen.add(key)
        profiles.append(
            {
                "username": name[:200],
                "platform": "facebook",
                "followers": int(item.get("likes") or item.get("followers") or item.get("fans") or 0),
                "bio": (item.get("about") or item.get("intro") or item.get("description") or "")[:2000],
                "profile_url": link or "",
                "snippet": (item.get("text") or "")[:500],
            }
        )
        if len(profiles) >= max_results:
            break
    return profiles


def extract_email_from_text(text: str) -> Optional[str]:
    if not text:
        return None
    m = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)
    return m.group(0) if m else None


def discover_youtube_channels_category(category: str, max_results: int) -> List[Dict[str, Any]]:
    if not YOUTUBE_API_KEY:
        return []
    discovered: List[Dict[str, Any]] = []
    max_q = 2 if AGENT_YOUTUBE_FAST else 5
    queries = youtube_queries_for_category(category, max_queries=max_q)
    per_cap = 8 if AGENT_YOUTUBE_FAST else 25
    per_q = max(1, min(per_cap, max_results // max(1, len(queries))))
    for query in queries:
        try:
            search_resp = requests.get(
                "https://www.googleapis.com/youtube/v3/search",
                params={
                    "part": "snippet",
                    "type": "channel",
                    "maxResults": per_q,
                    "q": query,
                    "key": YOUTUBE_API_KEY,
                    "relevanceLanguage": "fr",
                    "regionCode": "HT",
                },
                timeout=25,
            )
            if search_resp.status_code >= 400:
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
                timeout=25,
            )
            if channels_resp.status_code >= 400:
                continue
            for ch in channels_resp.json().get("items", []):
                sn = ch.get("snippet", {})
                st = ch.get("statistics", {})
                title = (sn.get("title") or "YouTube").strip()
                desc = (sn.get("description") or "")[:2000]
                cid = ch.get("id", "")
                handle = (sn.get("customUrl") or "").lstrip("@")
                url = f"https://www.youtube.com/channel/{cid}" if cid else ""
                if handle:
                    url = f"https://www.youtube.com/@{handle}"
                discovered.append(
                    {
                        "username": title,
                        "platform": "youtube",
                        "followers": int(st.get("subscriberCount") or 0),
                        "bio": desc,
                        "profile_url": url,
                        "snippet": desc[:500],
                    }
                )
        except Exception as e:
            logger.warning("YouTube discovery: %s", e)
    # dedupe by username
    uniq: Dict[str, Dict[str, Any]] = {}
    for p in discovered:
        k = p["username"].lower()
        if k not in uniq:
            uniq[k] = p
    return list(uniq.values())[:max_results]


CREOLE_ANALYSIS_SYSTEM = """Ou se yon espesyalis lingwistik ki idantifye si yon kreyatè kontni pale KREYÒL AYISYEN (Haitian Creole).

Baz ou sou: bio, tit, deskripsyon, hashtags, epi echantiyon tèks.

Endikatè pozitif (kreyòl): mo tankou "mwen", "nou", "li", "yo", "se", "gen", "ap", "nan", "yon", "men", "kòm",
"ayiti", "ayisyen", "kreyòl", "kreyol", "lekòl", "aprann", "fòmasyon", "an kreyòl", " pale kreyòl ".

Atansyon: franse ("nous", "votre", "bonjour") oswa angle pur san siy kreyòl = score ba.

Reponn UNIQUEMENT ak JSON valide:
{"creole_score": <0-100 entye>, "reasoning": "<kout eksplikasyon an kreyòl oswa franse kout>"}

creole_score:
- 90-100: kleman kreyòl ayisyen dominan
- 70-89: anpil kreyòl ak kek melanj
- 50-69: melanje / pa klè
- 0-49: pa kreyòl ayisyen oswa lòt lang dominan"""


def creole_keyword_boost(profile: Dict[str, Any]) -> int:
    """Sipò determinis: mo kle kreyòl / Ayiti nan tèks la."""
    t = (
        f"{profile.get('username','')} {profile.get('bio','')} {profile.get('snippet','')} "
        f"{profile.get('content_sample','')}"
    ).lower()
    markers = (
        "mwen ", " nou ", " li ", " yo ", "ayiti", "kreyòl", "kreyol", "lekòl", "aprann",
        " fòk ", " se ", " gen ", " nan ", " yon ", " men ", "ap ", "bonjou", " saly ", " n ", " an ",
    )
    hits = sum(1 for m in markers if m in t or t.strip().startswith(m.strip()))
    return min(55, hits * 7)


async def analyze_creole_score(openai_client: Any, model: str, profile: Dict[str, Any]) -> Dict[str, Any]:
    if not openai_client:
        kw_only = creole_keyword_boost(profile)
        return {"creole_score": kw_only, "reasoning": "OpenAI pa konfigire; sèlman endikatè mo kle."}
    text = f"""Username: {profile.get('username','')}
Platfòm: {profile.get('platform','')}
Bio: {profile.get('bio','')}
Echantiyon: {profile.get('snippet','') or profile.get('content_sample','')}"""
    try:
        completion = await openai_client.chat.completions.create(
            model=model,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": CREOLE_ANALYSIS_SYSTEM},
                {"role": "user", "content": text},
            ],
        )
        raw = (completion.choices[0].message.content or "{}").strip()
        data = json.loads(raw)
        score = int(data.get("creole_score", 0) or 0)
        score = max(0, min(100, score))
        kw = creole_keyword_boost(profile)
        score = max(score, kw)
        score = min(100, score)
        return {"creole_score": score, "reasoning": str(data.get("reasoning", "")).strip()}
    except Exception as e:
        logger.exception("Analiz kreyòl echwe: %s", e)
        kw = creole_keyword_boost(profile)
        return {"creole_score": kw, "reasoning": str(e)}


EMAIL_RECRUIT_SYSTEM = """Ou ekri imèl rekritman pou KonekteGroup an KREYÒL AYISYEN 100%.
- Adrese moun nan respekte
- Site domèn ekspertiz (kategori) a
- Envite l rejoind KonekteGroup kòm fòmatè / kreyatè
- Enkli lyen: https://konektegroup.com
- 4-7 fraz, pwofesyonèl, pa spam
- Sijè: kout, an kreyòl
Reponn ak JSON: {"subject": "...", "body": "..."}"""


async def generate_recruitment_email_openai(
    openai_client: Any, model: str, profile: Dict[str, Any]
) -> Dict[str, str]:
    if not openai_client:
        subj = "KonekteGroup — opòtinite fòmasyon"
        body = (
            f"Bonjou {profile.get('username','')},\n\n"
            f"Ekip KonekteGroup ap chèche fòmatè nan domèn {profile.get('category','')}.\n"
            f"Tanpri vizite https://konektegroup.com pou plis enfòmasyon.\n\n"
            "Respè,"
        )
        return {"subject": subj, "body": body}
    user = f"""Non oswa username: {profile.get('username','')}
Kategori: {profile.get('category','')}
Platfòm: {profile.get('platform','')}
Bio: {profile.get('bio','')[:1200]}
"""
    try:
        completion = await openai_client.chat.completions.create(
            model=model,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": EMAIL_RECRUIT_SYSTEM},
                {"role": "user", "content": user},
            ],
        )
        raw = (completion.choices[0].message.content or "{}").strip()
        data = json.loads(raw)
        return {
            "subject": (data.get("subject") or "KonekteGroup").strip()[:200],
            "body": (data.get("body") or "").strip(),
        }
    except Exception as e:
        logger.exception("Jenere imèl: %s", e)
        subj = "KonekteGroup — opòtinite fòmasyon"
        body = (
            f"Bonjou {profile.get('username','')},\n\n"
            f"Ekip KonekteGroup ap chèche fòmatè nan domèn {profile.get('category','')}.\n"
            f"Tanpri vizite https://konektegroup.com pou plis enfòmasyon.\n\n"
            "Respè,\nEkip KonekteGroup"
        )
        return {"subject": subj, "body": body}


def send_email_resend(to_email: str, subject: str, body: str) -> tuple[bool, str]:
    if not RESEND_API_KEY:
        return False, "RESEND_API_KEY manke"
    try:
        r = requests.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {RESEND_API_KEY}", "Content-Type": "application/json"},
            json={"from": RESEND_FROM, "to": [to_email], "subject": subject, "text": body},
            timeout=30,
        )
        if r.status_code >= 400:
            return False, (r.text or r.reason)[:500]
        return True, r.json().get("id", "ok")
    except Exception as e:
        return False, str(e)


def build_agent_profile_dict(
    *,
    username: str,
    platform: str,
    category: str,
    followers: int,
    bio: str,
    profile_url: str,
    email: Optional[str],
    creole_score: int,
    status: str,
    pid: Optional[str] = None,
) -> Dict[str, Any]:
    return {
        "id": pid or str(uuid.uuid4()),
        "username": username,
        "platform": platform.lower(),
        "category": category,
        "followers": int(followers or 0),
        "bio": bio or "",
        "profile_url": profile_url or "",
        "email": email,
        "creole_score": int(creole_score or 0),
        "status": status,
        "created_at": utc_now_iso(),
    }
