import json, sqlite3
from datetime import datetime, timezone

def insert(conn, kind, payload, result, trip_id=None, vehicle_id=None, plate=None):
    now = datetime.now(timezone.utc).isoformat()
    cur = conn.execute(
        "INSERT INTO calc_runs(kind,trip_id,vehicle_id,plate,input_json,result_json,created_at) VALUES (?,?,?,?,?,?,?)",
        (kind, trip_id, vehicle_id, plate, json.dumps(payload, ensure_ascii=False), json.dumps(result, ensure_ascii=False), now),
    )
    conn.commit()
    return int(cur.lastrowid)

def list_recent(conn, limit=50, plate=None):
    sql = "SELECT * FROM calc_runs"
    params: list = []
    if plate:
        sql += " WHERE plate=?"
        params.append(plate)
    sql += " ORDER BY id DESC LIMIT ?"
    params.append(limit)
    return [dict(r) for r in conn.execute(sql, params).fetchall()]
