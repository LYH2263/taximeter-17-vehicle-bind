import json, sqlite3
from datetime import datetime, timezone

def insert(conn, kind, payload, result, trip_id=None, plate=None):
    now = datetime.now(timezone.utc).isoformat()
    cur = conn.execute(
        "INSERT INTO calc_runs(kind,trip_id,input_json,result_json,created_at,plate) VALUES (?,?,?,?,?,?)",
        (kind, trip_id, json.dumps(payload, ensure_ascii=False), json.dumps(result, ensure_ascii=False), now, plate),
    )
    conn.commit()
    return int(cur.lastrowid)

def list_recent(conn, limit=50, plate=None):
    if plate:
        rows = conn.execute("SELECT * FROM calc_runs WHERE plate=? ORDER BY id DESC LIMIT ?", (plate, limit)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM calc_runs ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    return [dict(r) for r in rows]

def count(conn, plate=None):
    if plate:
        return conn.execute("SELECT COUNT(*) c FROM calc_runs WHERE plate=?", (plate,)).fetchone()["c"]
    return conn.execute("SELECT COUNT(*) c FROM calc_runs").fetchone()["c"]
