from __future__ import annotations

from datetime import UTC, datetime

import httpx

from rare_bird_alerts.models import Observation, Settings

EMBED_COLOR = 0x2D7D2D  # green accent
MAX_EMBEDS_PER_MESSAGE = 10


def build_embeds(observations: list[Observation]) -> list[dict]:
    """Convert observations into Discord embed dicts."""
    embeds = []
    for obs in observations:
        embed: dict = {
            "title": obs.com_name,
            "description": f"*{obs.sci_name}*",
            "url": obs.checklist_url,
            "color": EMBED_COLOR,
            "fields": [
                {"name": "Location", "value": obs.loc_name, "inline": True},
                {"name": "Date", "value": obs.obs_dt, "inline": True},
            ],
        }
        if obs.how_many is not None:
            embed["fields"].append({"name": "Count", "value": str(obs.how_many), "inline": True})
        if obs.image_url:
            embed["image"] = {"url": obs.image_url}
        embeds.append(embed)
    return embeds


def _build_header_embed(region: str, date: str, count: int) -> dict:
    """Build a header embed with summary info."""
    return {
        "title": "Rare Bird Alert",
        "description": f"**{region}** — {date} — {count} species",
        "color": EMBED_COLOR,
    }


async def send_discord_alert(
    settings: Settings,
    observations: list[Observation],
    region: str,
    date: str | None = None,
    *,
    client: httpx.AsyncClient | None = None,
) -> None:
    """Post rare bird alert embeds to a Discord webhook."""
    if date is None:
        date = datetime.now(tz=UTC).strftime("%B %d, %Y")

    should_close = client is None
    client = client or httpx.AsyncClient()

    try:
        if not observations:
            payload = {
                "embeds": [
                    _build_header_embed(region, date, 0),
                    {
                        "description": "No notable sightings today.",
                        "color": EMBED_COLOR,
                    },
                ]
            }
            resp = await client.post(settings.discord_webhook_url, json=payload, timeout=30.0)
            resp.raise_for_status()
            return

        bird_embeds = build_embeds(observations)
        header = _build_header_embed(region, date, len(observations))

        # First batch includes the header embed
        all_embeds = [header, *bird_embeds]

        for i in range(0, len(all_embeds), MAX_EMBEDS_PER_MESSAGE):
            batch = all_embeds[i : i + MAX_EMBEDS_PER_MESSAGE]
            resp = await client.post(
                settings.discord_webhook_url, json={"embeds": batch}, timeout=30.0
            )
            resp.raise_for_status()
    finally:
        if should_close:
            await client.aclose()
