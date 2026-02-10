# Playtomic Slot Monitor

Monitors padel court availability in Warsaw via the Playtomic API. Scans periodically, stores results in SQLite, runs custom SQL filters, and sends email alerts for newly available slots.

## Usage

```bash
# Discover available venues
python monitor.py --discover

# Run the monitor loop
python monitor.py
```

## Configuration

- **Venues** — edit the `VENUES` list in `monitor.py` (use `--discover` to find tenant IDs)
- **Filters** — define alert rules in `filters.sql` using `-- Alert: name` headers (queries run against `new_slots` table)
- **Email (Gmail)** — add credentials to `email_credentials/credentials.json` (see `email_setup.md`)
- **Email (Resend)** — set `RESEND_API_KEY` and `ALERT_TO` env vars (used on Railway/cloud)

## Alert behavior

- **First scan** (fresh DB): all matching slots are treated as new and trigger alerts
- **Subsequent scans**: only newly appeared slots trigger alerts
- If no new slots match the filters, no email is sent

## Docker

```bash
docker build -t playtomic-monitor .
docker run -d --name playtomic-monitor \
  -v playtomic-data:/app/data \
  -e GMAIL_USER="..." \
  -e GMAIL_APP_PASSWORD="..." \
  -e ALERT_TO="..." \
  playtomic-monitor
```

## Railway deployment

1. Deploy from GitHub repo on [Railway](https://railway.com)
2. Add a volume mounted at `/app/data`
3. Set environment variables: `RESEND_API_KEY`, `ALERT_TO`
4. Railway auto-deploys on each push to GitHub

Note: Railway free tier blocks SMTP (port 465), so Resend (HTTPS) is used instead of Gmail.

## Project structure

| File | Description |
|---|---|
| `monitor.py` | Entry point: config, CLI args, main loop |
| `api.py` | Playtomic API calls (venues, availability) |
| `scanner.py` | Scan logic and price parsing |
| `db.py` | SQLite init, storage, new-slot detection |
| `filters.py` | SQL filter parsing and execution |
| `alerts.py` | Email alerts via Resend (HTTPS) or Gmail (SMTP) |
| `filters.sql` | User-defined alert filter queries |
| `Dockerfile` | Container build for Docker / Railway |

## Database schema

`db.py` creates two tables in `playtomic.db`:

**scans** — one row per scan cycle

| Column | Type | Description |
|---|---|---|
| `id` | INTEGER PK | Auto-incremented record ID |
| `scan_id` | INTEGER | Sequential scan number (1, 2, 3, ...) |
| `scanned_at` | TEXT | Timestamp (Europe/Warsaw) |

**slots** — all available slots from the latest scan

| Column | Type | Description |
|---|---|---|
| `id` | INTEGER PK | Auto-incremented row ID |
| `venue` | TEXT | Venue name |
| `city` | TEXT | City |
| `address` | TEXT | Street address |
| `court` | TEXT | Court name |
| `court_type` | TEXT | indoor / outdoor |
| `court_size` | TEXT | single / double |
| `date` | DATE | Slot date |
| `weekday` | TEXT | Day of week (e.g. Monday) |
| `start_time` | TIME | Start time (Europe/Warsaw) |
| `duration_min` | INTEGER | Duration in minutes |
| `price_amount` | REAL | Price value |
| `currency` | TEXT | Currency code (e.g. PLN) |

**new_slots** — only newly appeared slots since the previous scan (filters run against this table)

## Requirements

- Python 3.9+
- `pip install -r requirements.txt` (`requests`, `resend`)
