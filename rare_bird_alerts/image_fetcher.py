from __future__ import annotations

import asyncio
import logging

import httpx

from rare_bird_alerts.models import Observation

logger = logging.getLogger(__name__)

WIKIPEDIA_API_URL = "https://en.wikipedia.org/w/api.php"
MAX_CONCURRENT_REQUESTS = 5


async def fetch_bird_image(
    species_name: str,
    *,
    client: httpx.AsyncClient | None = None,
) -> str | None:
    """Fetch the main Wikipedia image URL for a bird species by common name."""
    params = {
        "action": "query",
        "prop": "pageimages",
        "titles": species_name,
        "format": "json",
        "piprop": "thumbnail",
        "pithumbsize": 300,
    }

    should_close = client is None
    client = client or httpx.AsyncClient()
    try:
        resp = await client.get(WIKIPEDIA_API_URL, params=params, timeout=15.0)
        resp.raise_for_status()
        data = resp.json()
    except (httpx.HTTPError, ValueError):
        logger.warning("Failed to fetch image for %s", species_name)
        return None
    finally:
        if should_close:
            await client.aclose()

    pages = data.get("query", {}).get("pages", {})
    for page in pages.values():
        thumbnail = page.get("thumbnail")
        if thumbnail:
            return thumbnail["source"]
    return None


async def enrich_observations(observations: list[Observation]) -> list[Observation]:
    """Add image URLs to observations concurrently."""
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)

    async def _fetch(obs: Observation) -> Observation:
        async with semaphore, httpx.AsyncClient() as client:
            obs.image_url = await fetch_bird_image(obs.com_name, client=client)
        return obs

    return list(await asyncio.gather(*[_fetch(obs) for obs in observations]))
