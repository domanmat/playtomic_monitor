"""Email alerts: credential loading, formatting, and sending."""

import json
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

try:
    import resend as resend_sdk
except ImportError:
    resend_sdk = None

CREDENTIALS_PATH = Path(__file__).parent / "email_credentials" / "credentials.json"


def _load_credentials():
    """Load credentials from env vars first, then fall back to JSON file."""
    gmail_user = os.environ.get("GMAIL_USER", "")
    gmail_app_password = os.environ.get("GMAIL_APP_PASSWORD", "")
    alert_to = os.environ.get("ALERT_TO", "")

    if gmail_user and gmail_app_password and alert_to:
        return {"gmail_user": gmail_user, "gmail_app_password": gmail_app_password, "alert_to": alert_to}

    try:
        with open(CREDENTIALS_PATH, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


_creds = _load_credentials()
GMAIL_USER = _creds.get("gmail_user", "")
GMAIL_APP_PASSWORD = _creds.get("gmail_app_password", "")
ALERT_TO = os.environ.get("ALERT_TO", _creds.get("alert_to", ""))
RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
RESEND_FROM = os.environ.get("RESEND_FROM", "Playtomic Monitor <onboarding@resend.dev>")


def format_html_table(columns, rows):
    """Format query results as an HTML table."""
    html = '<table border="1" cellpadding="6" cellspacing="0" style="border-collapse:collapse; font-family:sans-serif; font-size:14px;">\n'
    html += "<tr>" + "".join(f"<th style='background:#f0f0f0'>{c}</th>" for c in columns) + "</tr>\n"
    for row in rows:
        html += "<tr>" + "".join(f"<td>{v}</td>" for v in row) + "</tr>\n"
    html += "</table>"
    return html


def _send_via_resend(subject, html_body, text):
    """Send email via Resend API (HTTPS, works on Railway free tier)."""
    resend_sdk.api_key = RESEND_API_KEY
    params = {
        "from": RESEND_FROM,
        "to": [ALERT_TO],
        "subject": subject,
        "html": html_body,
        "text": text,
    }
    resend_sdk.Emails.send(params)


def _send_via_gmail(subject, html_body, text):
    """Send email via Gmail SMTP."""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = GMAIL_USER
    msg["To"] = ALERT_TO
    msg.attach(MIMEText(text, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
        server.sendmail(GMAIL_USER, ALERT_TO, msg.as_string())


def send_alert(matches, db_path="playtomic.db"):
    """Send email alerts for matched filters. Uses Resend if configured, else Gmail."""
    use_resend = RESEND_API_KEY and resend_sdk and ALERT_TO
    use_gmail = GMAIL_USER and GMAIL_APP_PASSWORD and ALERT_TO

    if not use_resend and not use_gmail:
        print("  [WARN] No email provider configured — showing summary only")
        for m in matches:
            print(f"    {m['alert_name']}: {len(m['rows'])} matches")
        print(f"  Query playtomic.db for full results (e.g. sqlite3 {db_path})")
        return

    provider = "Resend" if use_resend else "Gmail"

    for m in matches:
        subject = f"Playtomic Alert: {m['alert_name']}"
        text = f"{m['alert_name']}\n\n{len(m['rows'])} matching slot(s) found.\n"
        html_body = f"<h3>{m['alert_name']}</h3>\n"
        html_body += f"<p>{len(m['rows'])} matching slot(s) found:</p>\n"
        html_body += format_html_table(m["columns"], m["rows"])

        try:
            if use_resend:
                _send_via_resend(subject, html_body, text)
            else:
                _send_via_gmail(subject, html_body, text)
            print(f"  Email sent via {provider}: {m['alert_name']} ({len(m['rows'])} matches)")
        except Exception as e:
            print(f"  [ERROR] Failed to send email for '{m['alert_name']}': {e}")
