from __future__ import annotations

import pytest
from pydantic import ValidationError

from rare_bird_alerts.models import Observation, Settings
from tests.conftest import SAMPLE_EBIRD_RESPONSE


class TestObservation:
    def test_parse_from_ebird_json(self) -> None:
        obs = Observation.model_validate(SAMPLE_EBIRD_RESPONSE[0])
        assert obs.species_code == "lbbgul"
        assert obs.com_name == "Lesser Black-backed Gull"
        assert obs.sci_name == "Larus fuscus"
        assert obs.loc_name == "Central Park"
        assert obs.obs_dt == "2026-03-19 14:30"
        assert obs.how_many == 2
        assert obs.lat == 40.7829
        assert obs.lng == -73.9654
        assert obs.obs_valid is True
        assert obs.location_private is False
        assert obs.sub_id == "S123456789"
        assert obs.image_url is None

    def test_checklist_url(self) -> None:
        obs = Observation.model_validate(SAMPLE_EBIRD_RESPONSE[0])
        assert obs.checklist_url == "https://ebird.org/checklist/S123456789"

    def test_how_many_optional(self) -> None:
        data = {**SAMPLE_EBIRD_RESPONSE[0]}
        del data["howMany"]
        obs = Observation.model_validate(data)
        assert obs.how_many is None

    def test_image_url_enrichment(self) -> None:
        obs = Observation.model_validate(SAMPLE_EBIRD_RESPONSE[0])
        obs.image_url = "https://example.com/bird.jpg"
        assert obs.image_url == "https://example.com/bird.jpg"

    def test_missing_required_field_raises(self) -> None:
        data = {**SAMPLE_EBIRD_RESPONSE[0]}
        del data["comName"]
        with pytest.raises(ValidationError):
            Observation.model_validate(data)


class TestSettings:
    def test_valid_settings(self, sample_settings: Settings) -> None:
        assert sample_settings.ebird_api_key == "test_key_123"
        assert sample_settings.region_code == "US-NY"
        assert sample_settings.days_back == 1
        assert sample_settings.discord_webhook_url == "https://discord.com/api/webhooks/test/test"

    def test_days_back_range(self) -> None:
        with pytest.raises(ValidationError):
            Settings(
                ebird_api_key="key",
                region_code="US",
                days_back=31,
                discord_webhook_url="https://discord.com/api/webhooks/x/y",
            )

    def test_days_back_zero_invalid(self) -> None:
        with pytest.raises(ValidationError):
            Settings(
                ebird_api_key="key",
                region_code="US",
                days_back=0,
                discord_webhook_url="https://discord.com/api/webhooks/x/y",
            )
