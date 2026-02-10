"""Database operations: init, store slots, detect new slots."""

from datetime import datetime
from zoneinfo import ZoneInfo


def init_db(conn):
    """Create tables if they don't exist."""
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS scans (
            scan_id    INTEGER PRIMARY KEY AUTOINCREMENT,
            scanned_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS slots (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            scan_id        INTEGER NOT NULL,
            venue          TEXT NOT NULL,
            city           TEXT,
            address        TEXT,
            court          TEXT,
            court_type     TEXT,
            date           DATE NOT NULL,
            weekday        TEXT,
            start_time     TIME NOT NULL,
            duration_min   INTEGER,
            price_amount   REAL,
            price_currency TEXT,
            FOREIGN KEY (scan_id) REFERENCES scans(scan_id)
        );
    """)


def store_slots(conn, slots):
    """Replace slots table with fresh scan data. Returns the scan_id.

    Before replacing, copies current slots into previous_slots for
    new-slot detection. The slots table only ever holds the latest scan.
    """
    cur = conn.cursor()

    # Record the scan
    cur.execute(
        "INSERT INTO scans (scanned_at) VALUES (?)",
        (datetime.now(ZoneInfo("Europe/Warsaw")).isoformat(),),
    )
    scan_id = cur.lastrowid

    # Archive current slots for comparison, then replace
    cur.execute("DROP TABLE IF EXISTS previous_slots")
    cur.execute("CREATE TABLE previous_slots AS SELECT * FROM slots")
    cur.execute("DELETE FROM slots")

    cur.executemany("""
        INSERT INTO slots (
            scan_id, venue, city, address, court, court_type,
            date, weekday, start_time, duration_min, price_amount, price_currency
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, [
        (
            scan_id,
            s["venue"], s["city"], s["address"], s["court"],
            s["court_type"],
            s["date"], s["weekday"], s["start_time"], s["duration_min"],
            s["price_amount"], s["price_currency"],
        )
        for s in slots
    ])

    conn.commit()
    return scan_id


def detect_new_slots(conn):
    """Return count of slots in current scan that weren't in the previous scan.
    Key = (venue, court, date, start_time, duration_min)."""
    # Check if previous_slots exists and has data
    cur = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='previous_slots'"
    )
    if not cur.fetchone():
        return 0

    cur = conn.execute("SELECT COUNT(*) FROM previous_slots")
    if cur.fetchone()[0] == 0:
        return 0

    cur = conn.execute("""
        SELECT COUNT(*) FROM slots s
        WHERE NOT EXISTS (
            SELECT 1 FROM previous_slots p
            WHERE p.venue = s.venue
              AND p.court = s.court
              AND p.date = s.date
              AND p.start_time = s.start_time
              AND p.duration_min = s.duration_min
        )
    """)
    return cur.fetchone()[0]
