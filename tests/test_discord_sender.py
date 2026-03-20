from __future__ import annotations

from unittest.mock import AsyncMock

import httpx
import pytest

from rare_bird_alerts.discord_sender import build_embeds, send_discord_alert
from rare_bird_alerts.models import Observation, Settings
from tests.conftest import SAMPLE_EBIRD_RESPONSE


class TestBuildEmbeds:
    def test_contains_bird_names(self, sample_observations: list[Observation]) -> None:
        embeds = build_embeds(sample_observations)
        titles = [e["title"] for e in embeds]
        assert "Lesser Black-backed Gull" in titles
        assert "Snow Goose" in titles

    def test_contains_scientific_names(self, sample_observations: list[Observation]) -> None:
        embeds = build_embeds(sample_observations)
        descriptions = [e["description"] for e in embeds]
        assert "*Larus fuscus*" in descriptions

    def test_contains_locations(self, sample_observations: list[Observation]) -> None:
        embeds = build_embeds(sample_observations)
        locations = [f["value"] for e in embeds for f in e["fields"] if f["name"] == "Location"]
        assert "Central Park" in locations
        assert "Jamaica Bay" in locations

    def test_contains_checklist_urls(self, sample_observations: list[Observation]) -> None:
        embeds = build_embeds(sample_observations)
        urls = [e["url"] for e in embeds]
        assert "https://ebird.org/checklist/S123456789" in urls

    def test_thumbnail_included_when_image_present(self) -> None:
        obs = Observation.model_validate(SAMPLE_EBIRD_RESPONSE[0])
        obs.image_url = "https://example.com/bird.jpg"
        embeds = build_embeds([obs])
        assert embeds[0]["thumbnail"] == {"url": "https://example.com/bird.jpg"}

    def test_thumbnail_omitted_when_no_image(self) -> None:
        obs = Observation.model_validate(SAMPLE_EBIRD_RESPONSE[0])
        obs.image_url = None
        embeds = build_embeds([obs])
        assert "thumbnail" not in embeds[0]

    def test_count_field_present_when_how_many(self) -> None:
        obs = Observation.model_validate(SAMPLE_EBIRD_RESPONSE[0])
        embeds = build_embeds([obs])
        field_names = [f["name"] for f in embeds[0]["fields"]]
        assert "Count" in field_names

    def test_count_field_omitted_when_no_how_many(self) -> None:
        data = {**SAMPLE_EBIRD_RESPONSE[0]}
        del data["howMany"]
        obs = Observation.model_validate(data)
        embeds = build_embeds([obs])
        field_names = [f["name"] for f in embeds[0]["fields"]]
        assert "Count" not in field_names

    def test_empty_observations(self) -> None:
        embeds = build_embeds([])
        assert embeds == []

    def test_embed_color(self, sample_observations: list[Observation]) -> None:
        embeds = build_embeds(sample_observations)
        assert all(e["color"] == 0x2D7D2D for e in embeds)


class TestSendDiscordAlert:
    async def test_posts_to_webhook(self, sample_settings: Settings) -> None:
        obs = [Observation.model_validate(SAMPLE_EBIRD_RESPONSE[0])]
        mock_response = httpx.Response(
            status_code=204,
            request=httpx.Request("POST", sample_settings.discord_webhook_url),
        )
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.post = AsyncMock(return_value=mock_response)

        await send_discord_alert(
            sample_settings, obs, "US-NY", "March 19, 2026", client=mock_client
        )

        mock_client.post.assert_called_once()
        call_kwargs = mock_client.post.call_args
        assert call_kwargs.args[0] == sample_settings.discord_webhook_url
        payload = call_kwargs.kwargs["json"]
        assert len(payload["embeds"]) == 2  # header + 1 bird

    async def test_header_embed_contains_region_and_date(self, sample_settings: Settings) -> None:
        obs = [Observation.model_validate(SAMPLE_EBIRD_RESPONSE[0])]
        mock_response = httpx.Response(
            status_code=204,
            request=httpx.Request("POST", sample_settings.discord_webhook_url),
        )
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.post = AsyncMock(return_value=mock_response)

        await send_discord_alert(
            sample_settings, obs, "US-NY", "March 19, 2026", client=mock_client
        )

        payload = mock_client.post.call_args.kwargs["json"]
        header = payload["embeds"][0]
        assert "US-NY" in header["description"]
        assert "March 19, 2026" in header["description"]
        assert "1 species" in header["description"]

    async def test_batching_over_10_species(self, sample_settings: Settings) -> None:
        # Create 12 unique species observations
        observations = []
        for i in range(12):
            data = {**SAMPLE_EBIRD_RESPONSE[0], "speciesCode": f"bird{i}"}
            observations.append(Observation.model_validate(data))

        mock_response = httpx.Response(
            status_code=204,
            request=httpx.Request("POST", sample_settings.discord_webhook_url),
        )
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.post = AsyncMock(return_value=mock_response)

        await send_discord_alert(
            sample_settings, observations, "US-NY", "March 19, 2026", client=mock_client
        )

        # 13 total embeds (1 header + 12 birds) → 2 batches (10 + 3)
        assert mock_client.post.call_count == 2
        first_batch = mock_client.post.call_args_list[0].kwargs["json"]["embeds"]
        second_batch = mock_client.post.call_args_list[1].kwargs["json"]["embeds"]
        assert len(first_batch) == 10
        assert len(second_batch) == 3

    async def test_empty_observations_sends_no_sightings(self, sample_settings: Settings) -> None:
        mock_response = httpx.Response(
            status_code=204,
            request=httpx.Request("POST", sample_settings.discord_webhook_url),
        )
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.post = AsyncMock(return_value=mock_response)

        await send_discord_alert(
            sample_settings, [], "US-NY", "March 19, 2026", client=mock_client
        )

        mock_client.post.assert_called_once()
        payload = mock_client.post.call_args.kwargs["json"]
        descriptions = [e.get("description", "") for e in payload["embeds"]]
        assert any("No notable sightings" in d for d in descriptions)

    async def test_http_error_raises(self, sample_settings: Settings) -> None:
        mock_response = httpx.Response(
            status_code=400,
            request=httpx.Request("POST", sample_settings.discord_webhook_url),
        )
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.post = AsyncMock(return_value=mock_response)

        with pytest.raises(httpx.HTTPStatusError):
            await send_discord_alert(
                sample_settings, [], "US-NY", "March 19, 2026", client=mock_client
            )

    async def test_default_date(self, sample_settings: Settings) -> None:
        mock_response = httpx.Response(
            status_code=204,
            request=httpx.Request("POST", sample_settings.discord_webhook_url),
        )
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.post = AsyncMock(return_value=mock_response)

        await send_discord_alert(sample_settings, [], "US-NY", client=mock_client)

        payload = mock_client.post.call_args.kwargs["json"]
        header = payload["embeds"][0]
        assert "202" in header["description"]  # Contains a year
