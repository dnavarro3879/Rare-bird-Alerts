from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime

from rare_bird_alerts.discord_sender import send_discord_alert
from rare_bird_alerts.ebird_client import deduplicate_observations, fetch_notable_observations
from rare_bird_alerts.image_fetcher import enrich_observations
from rare_bird_alerts.models import Settings

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


async def run() -> None:
    settings = Settings()  # type: ignore[call-arg]

    logger.info(
        "Fetching notable observations for %s (past %d day(s))…",
        settings.region_code,
        settings.days_back,
    )
    observations = await fetch_notable_observations(settings)
    logger.info("Got %d raw observations", len(observations))

    observations = deduplicate_observations(observations)
    logger.info("Deduplicated to %d unique species", len(observations))

    logger.info("Fetching bird images from Wikipedia…")
    observations = await enrich_observations(observations)
    images_found = sum(1 for o in observations if o.image_url)
    logger.info("Found images for %d/%d species", images_found, len(observations))

    today = datetime.now(tz=UTC).strftime("%B %d, %Y")
    logger.info("Posting alert to Discord…")
    await send_discord_alert(settings, observations, settings.region_code, today)
    logger.info("Done!")


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
