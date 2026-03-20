from __future__ import annotations

import smtplib
from datetime import UTC, datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from jinja2 import Template

from rare_bird_alerts.models import Observation, Settings

EMAIL_TEMPLATE = Template("""\
<!DOCTYPE html>
<html>
<head>
<style>
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
         background: #f5f5f5; margin: 0; padding: 20px; }
  .container { max-width: 680px; margin: 0 auto; }
  h1 { color: #2d5016; font-size: 24px; }
  .subtitle { color: #666; font-size: 14px; margin-bottom: 24px; }
  .card { background: #fff; border-radius: 8px; padding: 16px;
          margin-bottom: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
  .card-inner { display: flex; gap: 16px; }
  .bird-img { width: 120px; height: 120px; object-fit: cover; border-radius: 6px;
              flex-shrink: 0; }
  .placeholder { width: 120px; height: 120px; border-radius: 6px;
                 background: #e8f0e0; display: flex; align-items: center;
                 justify-content: center; font-size: 40px; flex-shrink: 0; }
  .details { flex: 1; }
  .bird-name { font-size: 18px; font-weight: 600; color: #1a1a1a; margin: 0 0 2px; }
  .sci-name { font-size: 13px; color: #888; font-style: italic; margin: 0 0 8px; }
  .meta { font-size: 13px; color: #555; line-height: 1.6; }
  .meta strong { color: #333; }
  a { color: #2d7d2d; }
  .footer { text-align: center; color: #999; font-size: 12px; margin-top: 24px; }
</style>
</head>
<body>
<div class="container">
  <h1>Rare Bird Alert</h1>
  <div class="subtitle">{{ region }} &mdash; {{ date }} &mdash; {{ count }} species</div>
  {% for obs in observations %}
  <div class="card">
    <div class="card-inner">
      {% if obs.image_url %}
      <img class="bird-img" src="{{ obs.image_url }}" alt="{{ obs.com_name }}">
      {% else %}
      <div class="placeholder">🐦</div>
      {% endif %}
      <div class="details">
        <p class="bird-name">{{ obs.com_name }}</p>
        <p class="sci-name">{{ obs.sci_name }}</p>
        <div class="meta">
          <strong>Location:</strong> {{ obs.loc_name }}<br>
          <strong>Date:</strong> {{ obs.obs_dt }}<br>
          {% if obs.how_many %}
          <strong>Count:</strong> {{ obs.how_many }}<br>
          {% endif %}
          <a href="{{ obs.checklist_url }}">View checklist &rarr;</a>
        </div>
      </div>
    </div>
  </div>
  {% endfor %}
  {% if not observations %}
  <div class="card">
    <p style="text-align:center; color:#888;">No notable sightings today.</p>
  </div>
  {% endif %}
  <div class="footer">
    Powered by <a href="https://ebird.org">eBird</a> &amp;
    <a href="https://www.wikipedia.org">Wikipedia</a>
  </div>
</div>
</body>
</html>
""")


def build_email_html(
    observations: list[Observation],
    region: str,
    date: str | None = None,
) -> str:
    """Render the alert email as HTML."""
    if date is None:
        date = datetime.now(tz=UTC).strftime("%B %d, %Y")
    return EMAIL_TEMPLATE.render(
        observations=observations,
        region=region,
        date=date,
        count=len(observations),
    )


def send_email(settings: Settings, subject: str, html_body: str) -> None:
    """Send an HTML email via SMTP/TLS."""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.email_from
    msg["To"] = ", ".join(settings.email_to)
    msg.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
        server.starttls()
        server.login(settings.smtp_user, settings.smtp_password)
        server.sendmail(settings.email_from, settings.email_to, msg.as_string())
