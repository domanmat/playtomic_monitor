# Playtomic Slot Monitor

Monitors padel court availability in Warsaw via the Playtomic API. Scans periodically, stores results in SQLite, runs custom SQL filters, and sends email alerts when matching slots are found.

## Usage

```bash
# Discover available venues
python monitor.py --discover

# Run the monitor loop
python monitor.py
```

## Configuration

- **Venues** — edit the `VENUES` list in `monitor.py` (use `--discover` to find tenant IDs)
- **Filters** — define alert rules in `filters.sql` using `-- Alert: name` headers
- **Email** — add Gmail credentials to `email_credentials/credentials.json` (see `email_setup.md`)

## Project structure

| File | Description |
|---|---|
| `monitor.py` | Entry point: config, CLI args, main loop |
| `api.py` | Playtomic API calls (venues, availability) |
| `scanner.py` | Scan logic and price parsing |
| `db.py` | SQLite init, storage, new-slot detection |
| `filters.py` | SQL filter parsing and execution |
| `alerts.py` | Email alert formatting and sending |
| `filters.sql` | User-defined alert filter queries |

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

## Requirements

- Python 3.9+
- `requests` (`pip install requests`)
