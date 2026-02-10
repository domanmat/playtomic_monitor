"""SQL filter parsing and execution."""

import re
import sqlite3


def parse_filters(path):
    """Parse filters.sql into list of (alert_name, sql_query) tuples."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        print(f"  [WARN] {path} not found, skipping filters")
        return []

    filters = []
    blocks = re.split(r"^(-- Alert:.+)$", content, flags=re.MULTILINE)

    # blocks looks like: ['', '-- Alert: ...', 'SQL...', '-- Alert: ...', 'SQL...']
    i = 1
    while i < len(blocks):
        alert_name = blocks[i].replace("-- Alert:", "").strip()
        sql = blocks[i + 1].strip() if i + 1 < len(blocks) else ""
        if sql:
            filters.append((alert_name, sql))
        i += 2

    return filters


def run_filters(conn, filters_path, table="new_slots"):
    """Run each filter query against the given table (default: new_slots)."""
    filters = parse_filters(filters_path)
    if not filters:
        return []

    matches = []
    for alert_name, sql in filters:
        sql = sql.replace("new_slots", table)
        try:
            cur = conn.execute(sql)
            columns = [desc[0] for desc in cur.description] if cur.description else []
            rows = cur.fetchall()
            if rows:
                matches.append({
                    "alert_name": alert_name,
                    "columns": columns,
                    "rows": rows,
                })
        except sqlite3.Error as e:
            print(f"  [ERROR] Filter '{alert_name}': {e}")

    return matches
