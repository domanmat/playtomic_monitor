"""Email alerts: credential loading, formatting, and sending."""

import json
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

CREDENTIALS_PATH = Path(__file__).parent / "email_credentials" / "credentials.json"


def _load_credentials():
    try:
        with open(CREDENTIALS_PATH, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


_creds = _load_credentials()
GMAIL_USER = _creds.get("gmail_user", "")
GMAIL_APP_PASSWORD = _creds.get("gmail_app_password", "")
ALERT_TO = _creds.get("alert_to", "")


def format_html_table(columns, rows):
    """Format query results as an HTML table."""
    html = '<table border="1" cellpadding="6" cellspacing="0" style="border-collapse:collapse; font-family:sans-serif; font-size:14px;">\n'
    html += "<tr>" + "".join(f"<th style='background:#f0f0f0'>{c}</th>" for c in columns) + "</tr>\n"
    for row in rows:
        html += "<tr>" + "".join(f"<td>{v}</td>" for v in row) + "</tr>\n"
    html += "</table>"
    return html


def send_alert(matches, db_path="playtomic.db"):
    """Send email alerts for matched filters."""
    if not GMAIL_USER or not GMAIL_APP_PASSWORD or not ALERT_TO:
        print("  [WARN] Gmail not configured — skipping email, showing summary only")
        for m in matches:
            print(f"    {m['alert_name']}: {len(m['rows'])} matches")
        print(f"  Query playtomic.db for full results (e.g. sqlite3 {db_path})")
        return

    for m in matches:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"Playtomic Alert: {m['alert_name']}"
        msg["From"] = GMAIL_USER
        msg["To"] = ALERT_TO

        text = f"{m['alert_name']}\n\n{len(m['rows'])} matching slot(s) found.\n"
        html_body = f"<h3>{m['alert_name']}</h3>\n"
        html_body += f"<p>{len(m['rows'])} matching slot(s) found:</p>\n"
        html_body += format_html_table(m["columns"], m["rows"])

        msg.attach(MIMEText(text, "plain"))
        msg.attach(MIMEText(html_body, "html"))

        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
                server.sendmail(GMAIL_USER, ALERT_TO, msg.as_string())
            print(f"  Email sent: {m['alert_name']} ({len(m['rows'])} matches)")
        except Exception as e:
            print(f"  [ERROR] Failed to send email for '{m['alert_name']}': {e}")
