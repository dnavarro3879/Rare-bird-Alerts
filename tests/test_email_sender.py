from __future__ import annotations

from unittest.mock import MagicMock, patch

from rare_bird_alerts.email_sender import build_email_html, send_email
from rare_bird_alerts.models import Observation, Settings
from tests.conftest import SAMPLE_EBIRD_RESPONSE


class TestBuildEmailHtml:
    def test_contains_bird_names(self, sample_observations: list[Observation]) -> None:
        html = build_email_html(sample_observations, "US-NY", "March 19, 2026")
        assert "Lesser Black-backed Gull" in html
        assert "Snow Goose" in html

    def test_contains_scientific_names(self, sample_observations: list[Observation]) -> None:
        html = build_email_html(sample_observations, "US-NY", "March 19, 2026")
        assert "Larus fuscus" in html
        assert "Anser caerulescens" in html

    def test_contains_locations(self, sample_observations: list[Observation]) -> None:
        html = build_email_html(sample_observations, "US-NY", "March 19, 2026")
        assert "Central Park" in html
        assert "Jamaica Bay" in html

    def test_contains_checklist_links(self, sample_observations: list[Observation]) -> None:
        html = build_email_html(sample_observations, "US-NY", "March 19, 2026")
        assert "ebird.org/checklist/S123456789" in html

    def test_contains_region_and_date(self, sample_observations: list[Observation]) -> None:
        html = build_email_html(sample_observations, "US-NY", "March 19, 2026")
        assert "US-NY" in html
        assert "March 19, 2026" in html

    def test_contains_species_count(self, sample_observations: list[Observation]) -> None:
        html = build_email_html(sample_observations, "US-NY", "March 19, 2026")
        assert "3 species" in html

    def test_image_included_when_present(self) -> None:
        obs = Observation.model_validate(SAMPLE_EBIRD_RESPONSE[0])
        obs.image_url = "https://example.com/bird.jpg"
        html = build_email_html([obs], "US-NY")
        assert "https://example.com/bird.jpg" in html

    def test_placeholder_when_no_image(self) -> None:
        obs = Observation.model_validate(SAMPLE_EBIRD_RESPONSE[0])
        obs.image_url = None
        html = build_email_html([obs], "US-NY")
        assert "placeholder" in html

    def test_empty_observations(self) -> None:
        html = build_email_html([], "US-NY", "March 19, 2026")
        assert "No notable sightings today" in html
        assert "0 species" in html

    def test_default_date(self) -> None:
        html = build_email_html([], "US-NY")
        assert "202" in html  # Contains a year


class TestSendEmail:
    @patch("rare_bird_alerts.email_sender.smtplib.SMTP")
    def test_sends_email(self, mock_smtp_class: MagicMock, sample_settings: Settings) -> None:
        mock_server = MagicMock()
        mock_smtp_class.return_value.__enter__ = MagicMock(return_value=mock_server)
        mock_smtp_class.return_value.__exit__ = MagicMock(return_value=False)

        send_email(sample_settings, "Test Subject", "<p>Hello</p>")

        mock_smtp_class.assert_called_once_with("smtp.gmail.com", 587)
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with("test@gmail.com", "test_password")
        mock_server.sendmail.assert_called_once()

        call_args = mock_server.sendmail.call_args
        assert call_args[0][0] == "test@gmail.com"
        assert call_args[0][1] == ["recipient@example.com"]
        assert "Test Subject" in call_args[0][2]
        assert "<p>Hello</p>" in call_args[0][2]
