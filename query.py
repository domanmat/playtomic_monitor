"""Run a SQL file against playtomic.db and print results as a table.

Usage:
    python query.py                  # runs filters.sql
    python query.py my_query.sql     # runs a custom SQL file
"""

import sqlite3
import sys

DB_PATH = "playtomic.db"

sql_path = sys.argv[1] if len(sys.argv) > 1 else "filters.sql"

with open(sql_path, "r", encoding="utf-8") as f:
    content = f.read().strip()

statements = [s.strip() for s in content.split(";") if s.strip()]
sql = statements[0]
if len(statements) > 1:
    print(f"[WARN] Executed only 1st query, but detected {len(statements)} in {sql_path}\n")

conn = sqlite3.connect(DB_PATH)
cur = conn.execute(sql)
columns = [d[0] for d in cur.description]
rows = cur.fetchall()
conn.close()

if not rows:
    print("(no results)")
    sys.exit()

# Calculate column widths and print
widths = [max(len(c), *(len(str(r[i])) for r in rows)) for i, c in enumerate(columns)]
print(" | ".join(c.ljust(w) for c, w in zip(columns, widths)))
print("-+-".join("-" * w for w in widths))
for row in rows:
    print(" | ".join(str(v).ljust(w) for v, w in zip(row, widths)))
print(f"\n({len(rows)} rows)")
