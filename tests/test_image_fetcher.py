from __future__ import annotations

from unittest.mock import AsyncMock

import httpx
import pytest

from rare_bird_alerts.image_fetcher import enrich_observations, fetch_bird_image
from rare_bird_alerts.models import Observation
from tests.conftest import (
    SAMPLE_EBIRD_RESPONSE,
    SAMPLE_WIKIPEDIA_NO_IMAGE,
    SAMPLE_WIKIPEDIA_RESPONSE,
)


class TestFetchBirdImage:
    async def test_returns_image_url(self) -> None:
        mock_response = httpx.Response(
            status_code=200,
            json=SAMPLE_WIKIPEDIA_RESPONSE,
            request=httpx.Request("GET", "https://en.wikipedia.org/w/api.php"),
        )
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.get = AsyncMock(return_value=mock_response)

        url = await fetch_bird_image("Lesser Black-backed Gull", client=mock_client)
        assert url == "https://upload.wikimedia.org/wikipedia/commons/thumb/example.jpg"

    async def test_returns_none_when_no_image(self) -> None:
        mock_response = httpx.Response(
            status_code=200,
            json=SAMPLE_WIKIPEDIA_NO_IMAGE,
            request=httpx.Request("GET", "https://en.wikipedia.org/w/api.php"),
        )
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.get = AsyncMock(return_value=mock_response)

        url = await fetch_bird_image("Unknown Bird", client=mock_client)
        assert url is None

    async def test_returns_none_on_http_error(self) -> None:
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.get = AsyncMock(side_effect=httpx.ConnectError("connection refused"))

        url = await fetch_bird_image("Some Bird", client=mock_client)
        assert url is None

    async def test_request_params(self) -> None:
        mock_response = httpx.Response(
            status_code=200,
            json=SAMPLE_WIKIPEDIA_RESPONSE,
            request=httpx.Request("GET", "https://en.wikipedia.org/w/api.php"),
        )
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.get = AsyncMock(return_value=mock_response)

        await fetch_bird_image("Bald Eagle", client=mock_client)

        call_kwargs = mock_client.get.call_args.kwargs
        assert call_kwargs["params"]["titles"] == "Bald Eagle"
        assert call_kwargs["params"]["prop"] == "pageimages"
        assert call_kwargs["params"]["pithumbsize"] == 300


class TestEnrichObservations:
    async def test_enriches_all_observations(self) -> None:
        observations = [Observation.model_validate(SAMPLE_EBIRD_RESPONSE[0])]

        mock_response = httpx.Response(
            status_code=200,
            json=SAMPLE_WIKIPEDIA_RESPONSE,
            request=httpx.Request("GET", "https://en.wikipedia.org/w/api.php"),
        )

        with pytest.MonkeyPatch.context() as mp:

            async def mock_get(*args, **kwargs):
                return mock_response

            mp.setattr(httpx.AsyncClient, "get", mock_get)
            mp.setattr(httpx.AsyncClient, "aclose", AsyncMock())
            client = httpx.AsyncClient()
            mp.setattr(httpx.AsyncClient, "__aenter__", AsyncMock(return_value=client))
            mp.setattr(httpx.AsyncClient, "__aexit__", AsyncMock(return_value=False))

            result = await enrich_observations(observations)

        assert len(result) == 1
        assert result[0].image_url is not None
