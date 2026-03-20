# Rare Bird Alerts

Daily email digest of rare/notable bird sightings from [eBird](https://ebird.org), enriched with bird photos from Wikipedia.

## Setup

1. **Get an eBird API key** at https://ebird.org/api/keygen

2. **Create a Gmail App Password** (Google Account > Security > 2-Step Verification > App Passwords)

3. **Configure environment variables** — copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

4. **Install and run:**

```bash
uv sync
uv run rare-bird-alerts
```

## GitHub Actions (Daily Schedule)

This repo includes a workflow that runs the alert daily at 1pm UTC.

Add these secrets to your repo (Settings > Secrets and variables > Actions):

- `EBIRD_API_KEY` — your eBird API key
- `REGION_CODE` — eBird region code (e.g. `US-NY`, `US-CA-037`)
- `SMTP_USER` — your Gmail address
- `SMTP_PASSWORD` — your Gmail App Password
- `EMAIL_FROM` — sender email address
- `EMAIL_TO` — comma-separated recipient addresses
- `DAYS_BACK` (optional) — days to look back (default: 1, max: 30)

You can also trigger it manually from the Actions tab.

## Development

```bash
uv sync
uv run ruff check .
uv run ruff format --check .
uv run pytest --cov=rare_bird_alerts --cov-report=term-missing
```
