"""Database operations: init, store slots, detect new slots."""

from datetime import datetime
from zoneinfo import ZoneInfo


def init_db(conn):
    """Create tables if they don't exist."""
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS scans (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            scan_id    INTEGER NOT NULL,
            scanned_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS slots (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            venue          TEXT NOT NULL,
            city           TEXT,
            address        TEXT,
            court          TEXT,
            court_type     TEXT,
            court_size     TEXT,
            date           DATE NOT NULL,
            weekday        TEXT,
            start_time     TIME NOT NULL,
            duration_min   INTEGER,
            price_amount   REAL,
            currency       TEXT
        );
    """)


def store_slots(conn, slots):
    """Replace slots table with fresh scan data. Returns the scan_id.

    Before replacing, copies current slots into previous_slots for
    new-slot detection. The slots table only ever holds the latest scan.
    """
    cur = conn.cursor()

    # Determine next scan_id (max + 1, starting from 1)
    cur.execute("SELECT COALESCE(MAX(scan_id), 0) + 1 FROM scans")
    scan_id = cur.fetchone()[0]

    # Record the scan
    cur.execute(
        "INSERT INTO scans (scan_id, scanned_at) VALUES (?, ?)",
        (scan_id, datetime.now(ZoneInfo("Europe/Warsaw")).isoformat()),
    )

    # Archive current slots for comparison, then replace
    cur.execute("DROP TABLE IF EXISTS previous_slots")
    cur.execute("CREATE TABLE previous_slots AS SELECT * FROM slots")
    cur.execute("DELETE FROM slots")

    cur.executemany("""
        INSERT INTO slots (
            venue, city, address, court, court_type, court_size,
            date, weekday, start_time, duration_min, price_amount, currency
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, [
        (
            s["venue"], s["city"], s["address"], s["court"],
            s["court_type"], s["court_size"],
            s["date"], s["weekday"], s["start_time"], s["duration_min"],
            s["price_amount"], s["currency"],
        )
        for s in slots
    ])

    conn.commit()
    return scan_id


def populate_new_slots(conn):
    """Create/replace new_slots table with only newly appeared slots.

    On first scan (no previous_slots or empty): new_slots = all slots.
    On subsequent scans: new_slots = slots not in previous_slots.
    Key = (venue, court, date, start_time, duration_min).
    Returns the count of new slots.
    """
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS new_slots")

    # Check if previous_slots exists and has data
    cur.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='previous_slots'"
    )
    has_previous = cur.fetchone() is not None

    if has_previous:
        cur.execute("SELECT COUNT(*) FROM previous_slots")
        has_previous = cur.fetchone()[0] > 0

    if not has_previous:
        # First scan — all slots are new
        cur.execute("CREATE TABLE new_slots AS SELECT * FROM slots")
    else:
        # Subsequent scans — only slots not in previous scan
        cur.execute("""
            CREATE TABLE new_slots AS
            SELECT * FROM slots s
            WHERE NOT EXISTS (
                SELECT 1 FROM previous_slots p
                WHERE p.venue = s.venue
                  AND p.court = s.court
                  AND p.date = s.date
                  AND p.start_time = s.start_time
                  AND p.duration_min = s.duration_min
            )
        """)

    conn.commit()
    cur.execute("SELECT COUNT(*) FROM new_slots")
    return cur.fetchone()[0]
