"""
Playtomic Slot Monitor

Periodically fetches padel court availability from the Playtomic API,
stores it in SQLite, detects newly released slots, runs user-defined
SQL filters, and sends email alerts via Gmail.

Usage:
    python monitor.py --discover   # print all Warsaw venues with IDs
    python monitor.py              # run the monitor loop
"""

import argparse
import os
import sqlite3
import sys
import time
from datetime import datetime
from zoneinfo import ZoneInfo

from api import fetch_all_venues, fetch_venues
from scanner import scan_venues
from db import init_db, store_slots, populate_new_slots
from filters import run_filters
from alerts import send_alert

# ── Configuration ─────────────────────────────────────────────
# Venues to monitor (tenant_id list — run with --discover to find IDs)
VENUES = [
    "057c5f40-f54b-4e4d-977c-1f9547a25076",  # Interpadel Warszawa
    "e7284c78-e269-44ad-8f3d-a4d63089c80c",  # Warsaw Padel Club
]

SCAN_INTERVAL_MIN = 10
DB_PATH = os.environ.get("DB_PATH", "playtomic.db")
FILTERS_PATH = "filters.sql"


def discover():
    """Print all Warsaw venues with their tenant_ids."""
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore
    print("Fetching all padel venues in Warsaw...\n")
    venues = fetch_all_venues()
    print(f"Found {len(venues)} venues:\n")
    print(f"  {'#':>3}  {'tenant_id':<40} {'Name':<40} City")
    print(f"  {'─'*3}  {'─'*40} {'─'*40} {'─'*20}")
    for i, v in enumerate(venues, 1):
        courts = len(v["resource_map"])
        print(f"  {i:3d}  {v['tenant_id']:<40} {v['tenant_name']:<40} {v['city']} ({courts} courts)")

    print(f"\nCopy the tenant_id values you want to monitor into VENUES in monitor.py:")
    print(f'  VENUES = ["{venues[0]["tenant_id"]}"]' if venues else "  VENUES = []")


def main():
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore

    parser = argparse.ArgumentParser(description="Playtomic Slot Monitor")
    parser.add_argument("--discover", action="store_true",
                        help="Print all Warsaw venues with tenant_ids, then exit")
    args = parser.parse_args()

    if args.discover:
        discover()
        return

    if not VENUES:
        print("No venues configured. Run with --discover to find venue IDs,")
        print("then add them to the VENUES list in monitor.py.")
        return

    conn = sqlite3.connect(DB_PATH)
    init_db(conn)

    print(f"Playtomic Slot Monitor started")
    print(f"  Monitoring {len(VENUES)} venue(s)")
    print(f"  Scan interval: {SCAN_INTERVAL_MIN} minutes")
    print(f"  Database: {DB_PATH}")
    print(f"  Filters: {FILTERS_PATH}")
    print()

    try:
        while True:
            now = datetime.now(ZoneInfo("Europe/Warsaw"))
            print(f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] Starting scan...")

            # Fetch
            venues = fetch_venues(VENUES)
            print(f"  Fetched info for {len(venues)} venue(s)")
            slots = scan_venues(venues)
            print(f"  Found {len(slots)} available slots")

            # Store (replaces previous slots, keeps one scan only)
            scan_id = store_slots(conn, slots)
            print(f"  Stored as scan #{scan_id}")

            # Populate new_slots (first scan = all, subsequent = only new)
            new_count = populate_new_slots(conn)
            if new_count > 0:
                print(f"  {new_count} new slot(s) since last scan")
            else:
                print("  No new slots since last scan")

            # Run filters against new_slots only
            if new_count > 0:
                matches = run_filters(conn, FILTERS_PATH)
                if matches:
                    total = sum(len(m["rows"]) for m in matches)
                    print(f"  Filters matched {total} slot(s) across {len(matches)} alert(s)")
                    send_alert(matches, DB_PATH)
                else:
                    print("  No filter matches on new slots")
            else:
                print("  Skipping filters (no new slots)")

            print(f"  Next scan in {SCAN_INTERVAL_MIN} minutes\n")
            time.sleep(SCAN_INTERVAL_MIN * 60)

    except KeyboardInterrupt:
        print("\nMonitor stopped.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
