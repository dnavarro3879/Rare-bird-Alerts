from __future__ import annotations

import pytest

from rare_bird_alerts.models import Observation, Settings

SAMPLE_EBIRD_RESPONSE = [
    {
        "speciesCode": "lbbgul",
        "comName": "Lesser Black-backed Gull",
        "sciName": "Larus fuscus",
        "locId": "L123456",
        "locName": "Central Park",
        "obsDt": "2026-03-19 14:30",
        "howMany": 2,
        "lat": 40.7829,
        "lng": -73.9654,
        "obsValid": True,
        "obsReviewed": True,
        "locationPrivate": False,
        "subId": "S123456789",
    },
    {
        "speciesCode": "snogoo",
        "comName": "Snow Goose",
        "sciName": "Anser caerulescens",
        "locId": "L654321",
        "locName": "Jamaica Bay",
        "obsDt": "2026-03-19 09:15",
        "howMany": 15,
        "lat": 40.6167,
        "lng": -73.8253,
        "obsValid": True,
        "obsReviewed": False,
        "locationPrivate": False,
        "subId": "S987654321",
    },
    {
        "speciesCode": "lbbgul",
        "comName": "Lesser Black-backed Gull",
        "sciName": "Larus fuscus",
        "locId": "L789012",
        "locName": "Prospect Park",
        "obsDt": "2026-03-18 10:00",
        "howMany": 1,
        "lat": 40.6602,
        "lng": -73.9690,
        "obsValid": True,
        "obsReviewed": True,
        "locationPrivate": False,
        "subId": "S111222333",
    },
]

SAMPLE_WIKIPEDIA_RESPONSE = {
    "query": {
        "pages": {
            "12345": {
                "pageid": 12345,
                "title": "Lesser Black-backed Gull",
                "thumbnail": {
                    "source": "https://upload.wikimedia.org/wikipedia/commons/thumb/example.jpg",
                    "width": 300,
                    "height": 200,
                },
            }
        }
    }
}

SAMPLE_WIKIPEDIA_NO_IMAGE = {
    "query": {
        "pages": {
            "-1": {
                "ns": 0,
                "title": "Unknown Bird",
                "missing": "",
            }
        }
    }
}


@pytest.fixture
def sample_observations() -> list[Observation]:
    return [Observation.model_validate(item) for item in SAMPLE_EBIRD_RESPONSE]


@pytest.fixture
def sample_settings() -> Settings:
    return Settings(
        ebird_api_key="test_key_123",
        region_code="US-NY",
        days_back=1,
        smtp_host="smtp.gmail.com",
        smtp_port=587,
        smtp_user="test@gmail.com",
        smtp_password="test_password",
        email_from="test@gmail.com",
        email_to=["recipient@example.com"],
    )
