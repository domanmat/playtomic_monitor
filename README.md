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

## Requirements

- Python 3.9+
- `requests` (`pip install requests`)
