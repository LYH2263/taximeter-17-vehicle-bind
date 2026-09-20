import sqlite3

def list_all(conn: sqlite3.Connection) -> list[dict]:
    return [dict(r) for r in conn.execute("SELECT * FROM vehicles ORDER BY id").fetchall()]

def get(conn: sqlite3.Connection, vid: int) -> dict | None:
    row = conn.execute("SELECT * FROM vehicles WHERE id=?", (vid,)).fetchone()
    return dict(row) if row else None

def find_enabled_by_plate(conn: sqlite3.Connection, plate: str, exclude_id: int | None = None) -> dict | None:
    if exclude_id is None:
        row = conn.execute("SELECT * FROM vehicles WHERE plate=? AND enabled=1 ORDER BY id LIMIT 1", (plate,)).fetchone()
    else:
        row = conn.execute("SELECT * FROM vehicles WHERE plate=? AND enabled=1 AND id<>? ORDER BY id LIMIT 1", (plate, exclude_id)).fetchone()
    return dict(row) if row else None

def create(conn: sqlite3.Connection, plate: str, enabled: bool) -> dict:
    cur = conn.execute("INSERT INTO vehicles(plate,enabled) VALUES (?,?)", (plate, 1 if enabled else 0))
    conn.commit()
    return get(conn, int(cur.lastrowid))

def update(conn: sqlite3.Connection, vid: int, plate: str, enabled: bool) -> dict | None:
    conn.execute("UPDATE vehicles SET plate=?, enabled=? WHERE id=?", (plate, 1 if enabled else 0, vid))
    conn.commit()
    return get(conn, vid)
