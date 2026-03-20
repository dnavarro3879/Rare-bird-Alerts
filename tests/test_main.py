from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

from rare_bird_alerts.main import run
from rare_bird_alerts.models import Observation
from tests.conftest import SAMPLE_EBIRD_RESPONSE


class TestRun:
    @patch("rare_bird_alerts.main.send_email")
    @patch("rare_bird_alerts.main.enrich_observations")
    @patch("rare_bird_alerts.main.fetch_notable_observations")
    @patch("rare_bird_alerts.main.Settings")
    async def test_full_pipeline(
        self,
        mock_settings_cls: MagicMock,
        mock_fetch: AsyncMock,
        mock_enrich: AsyncMock,
        mock_send: MagicMock,
    ) -> None:
        settings = MagicMock()
        settings.region_code = "US-NY"
        settings.days_back = 1
        settings.email_to = ["test@example.com"]
        mock_settings_cls.return_value = settings

        observations = [Observation.model_validate(item) for item in SAMPLE_EBIRD_RESPONSE]
        mock_fetch.return_value = observations

        enriched = [Observation.model_validate(SAMPLE_EBIRD_RESPONSE[0])]
        enriched[0].image_url = "https://example.com/img.jpg"
        mock_enrich.return_value = enriched

        await run()

        mock_fetch.assert_awaited_once_with(settings)
        mock_enrich.assert_awaited_once()
        mock_send.assert_called_once()

        send_args = mock_send.call_args
        assert send_args[0][0] is settings
        assert "Rare Bird Alert" in send_args[0][1]
        assert "US-NY" in send_args[0][1]

    @patch("rare_bird_alerts.main.send_email")
    @patch("rare_bird_alerts.main.enrich_observations")
    @patch("rare_bird_alerts.main.fetch_notable_observations")
    @patch("rare_bird_alerts.main.Settings")
    async def test_empty_observations(
        self,
        mock_settings_cls: MagicMock,
        mock_fetch: AsyncMock,
        mock_enrich: AsyncMock,
        mock_send: MagicMock,
    ) -> None:
        settings = MagicMock()
        settings.region_code = "US-CA"
        settings.days_back = 1
        settings.email_to = ["test@example.com"]
        mock_settings_cls.return_value = settings

        mock_fetch.return_value = []
        mock_enrich.return_value = []

        await run()

        mock_send.assert_called_once()
