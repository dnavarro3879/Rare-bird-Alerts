from __future__ import annotations

import httpx

from rare_bird_alerts.models import Observation, Settings

EBIRD_BASE_URL = "https://api.ebird.org/v2"


async def fetch_notable_observations(
    settings: Settings,
    *,
    client: httpx.AsyncClient | None = None,
) -> list[Observation]:
    """Fetch recent notable observations for the configured region."""
    url = f"{EBIRD_BASE_URL}/data/obs/{settings.region_code}/recent/notable"
    headers = {"x-ebirdapitoken": settings.ebird_api_key}
    params = {
        "back": settings.days_back,
        "detail": "full",
        "maxResults": 200,
    }

    should_close = client is None
    client = client or httpx.AsyncClient()
    try:
        resp = await client.get(url, headers=headers, params=params, timeout=30.0)
        resp.raise_for_status()
        data = resp.json()
    finally:
        if should_close:
            await client.aclose()

    return [Observation.model_validate(item) for item in data]


def deduplicate_observations(observations: list[Observation]) -> list[Observation]:
    """Keep only the most recent observation per species."""
    seen: dict[str, Observation] = {}
    for obs in observations:
        if obs.species_code not in seen or obs.obs_dt > seen[obs.species_code].obs_dt:
            seen[obs.species_code] = obs
    return list(seen.values())
