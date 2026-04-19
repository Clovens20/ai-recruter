"""Test local Apify TikTok — mettre APIFY_API_KEY dans .env (non versionné)."""
import os
from pathlib import Path

from apify_client import ApifyClient

ROOT = Path(__file__).resolve().parent
try:
    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env")
    load_dotenv(ROOT / "backend" / ".env")
except ImportError:
    pass

token = os.environ.get("APIFY_API_KEY", "").strip()
if not token:
    raise SystemExit("Définissez APIFY_API_KEY dans .env à la racine ou backend/.env")

client = ApifyClient(token)

run_input = {
    "hashtags": ["formateur"],
    "resultsPerPage": 5,
    "shouldDownloadVideos": False,
    "shouldDownloadCovers": False,
}

print("Recherche en cours...")
run = client.actor("clockworks/tiktok-scraper").call(run_input=run_input)

for item in client.dataset(run["defaultDatasetId"]).iterate_items():
    author = item.get("authorMeta", {})
    print(f"Auteur: {author.get('name')}")
    print(f"Followers: {author.get('fans')}")
    print(f"Bio: {author.get('signature')}")
    print("---")
