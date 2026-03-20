from __future__ import annotations

import asyncio
import logging

import httpx

from rare_bird_alerts.models import Observation

logger = logging.getLogger(__name__)

INATURALIST_API_URL = "https://api.inaturalist.org/v1/taxa"
MAX_CONCURRENT_REQUESTS = 5
USER_AGENT = "RareBirdAlerts/1.0 (https://github.com/rare-bird-alerts)"


async def fetch_bird_image(
    species_name: str,
    *,
    client: httpx.AsyncClient | None = None,
) -> str | None:
    """Fetch a bird photo URL from iNaturalist by common name."""
    params = {"q": species_name, "rank": "species", "per_page": 1}
    headers = {"User-Agent": USER_AGENT}

    should_close = client is None
    client = client or httpx.AsyncClient()
    try:
        resp = await client.get(
            INATURALIST_API_URL, params=params, headers=headers, timeout=15.0
        )
        resp.raise_for_status()
        data = resp.json()
    except (httpx.HTTPError, ValueError):
        logger.warning("Failed to fetch image for %s", species_name)
        return None
    finally:
        if should_close:
            await client.aclose()

    results = data.get("results", [])
    if results:
        photo = results[0].get("default_photo")
        if photo:
            # Use medium_url for a good balance of quality and size
            return photo.get("medium_url")
    return None


async def enrich_observations(observations: list[Observation]) -> list[Observation]:
    """Add image URLs to observations concurrently."""
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)

    async def _fetch(obs: Observation) -> Observation:
        async with semaphore, httpx.AsyncClient() as client:
            obs.image_url = await fetch_bird_image(obs.com_name, client=client)
        return obs

    return list(await asyncio.gather(*[_fetch(obs) for obs in observations]))
