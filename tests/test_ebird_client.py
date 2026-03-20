from __future__ import annotations

from unittest.mock import AsyncMock

import httpx
import pytest

from rare_bird_alerts.ebird_client import (
    deduplicate_observations,
    fetch_notable_observations,
)
from rare_bird_alerts.models import Observation, Settings
from tests.conftest import SAMPLE_EBIRD_RESPONSE


class TestFetchNotableObservations:
    async def test_successful_fetch(self, sample_settings: Settings) -> None:
        mock_response = httpx.Response(
            status_code=200,
            json=SAMPLE_EBIRD_RESPONSE,
            request=httpx.Request("GET", "https://api.ebird.org/v2/data/obs/US-NY/recent/notable"),
        )
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.get = AsyncMock(return_value=mock_response)

        result = await fetch_notable_observations(sample_settings, client=mock_client)

        assert len(result) == 3
        assert all(isinstance(o, Observation) for o in result)
        assert result[0].com_name == "Lesser Black-backed Gull"
        assert result[1].com_name == "Snow Goose"

    async def test_request_headers_and_params(self, sample_settings: Settings) -> None:
        mock_response = httpx.Response(
            status_code=200,
            json=[],
            request=httpx.Request("GET", "https://api.ebird.org/v2/data/obs/US-NY/recent/notable"),
        )
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.get = AsyncMock(return_value=mock_response)

        await fetch_notable_observations(sample_settings, client=mock_client)

        call_kwargs = mock_client.get.call_args
        assert "x-ebirdapitoken" in call_kwargs.kwargs["headers"]
        assert call_kwargs.kwargs["headers"]["x-ebirdapitoken"] == "test_key_123"
        assert call_kwargs.kwargs["params"]["back"] == 1
        assert call_kwargs.kwargs["params"]["detail"] == "full"

    async def test_http_error_raises(self, sample_settings: Settings) -> None:
        mock_response = httpx.Response(
            status_code=401,
            request=httpx.Request("GET", "https://api.ebird.org/v2/data/obs/US-NY/recent/notable"),
        )
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.get = AsyncMock(return_value=mock_response)

        with pytest.raises(httpx.HTTPStatusError):
            await fetch_notable_observations(sample_settings, client=mock_client)

    async def test_empty_response(self, sample_settings: Settings) -> None:
        mock_response = httpx.Response(
            status_code=200,
            json=[],
            request=httpx.Request("GET", "https://api.ebird.org/v2/data/obs/US-NY/recent/notable"),
        )
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.get = AsyncMock(return_value=mock_response)

        result = await fetch_notable_observations(sample_settings, client=mock_client)
        assert result == []


class TestDeduplicateObservations:
    def test_removes_duplicates_keeps_most_recent(
        self, sample_observations: list[Observation]
    ) -> None:
        result = deduplicate_observations(sample_observations)
        assert len(result) == 2

        species_codes = {o.species_code for o in result}
        assert species_codes == {"lbbgul", "snogoo"}

        gull = next(o for o in result if o.species_code == "lbbgul")
        assert gull.obs_dt == "2026-03-19 14:30"
        assert gull.loc_name == "Central Park"

    def test_empty_list(self) -> None:
        assert deduplicate_observations([]) == []

    def test_single_observation(self, sample_observations: list[Observation]) -> None:
        result = deduplicate_observations([sample_observations[0]])
        assert len(result) == 1
