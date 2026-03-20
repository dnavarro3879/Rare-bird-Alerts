from __future__ import annotations

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Observation(BaseModel):
    """A single notable bird observation from the eBird API."""

    species_code: str = Field(alias="speciesCode")
    com_name: str = Field(alias="comName")
    sci_name: str = Field(alias="sciName")
    loc_id: str = Field(alias="locId")
    loc_name: str = Field(alias="locName")
    obs_dt: str = Field(alias="obsDt")
    how_many: int | None = Field(default=None, alias="howMany")
    lat: float
    lng: float
    obs_valid: bool = Field(alias="obsValid")
    obs_reviewed: bool = Field(alias="obsReviewed")
    location_private: bool = Field(alias="locationPrivate")
    sub_id: str = Field(alias="subId")

    # Enrichment fields (not from eBird)
    image_url: str | None = None

    model_config = {"populate_by_name": True}

    @property
    def checklist_url(self) -> str:
        return f"https://ebird.org/checklist/{self.sub_id}"


class Settings(BaseSettings):
    """Application settings loaded from environment variables / .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    # eBird
    ebird_api_key: str
    region_code: str
    days_back: int = Field(default=1, ge=1, le=30)

    # SMTP (Gmail defaults)
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str
    smtp_password: str

    # Email
    email_from: str
    email_to: list[str]
