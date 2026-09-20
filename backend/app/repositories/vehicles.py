import sqlite3
from datetime import datetime, timezone


class VehicleConflict(Exception):
    """两条启用车辆车牌相同；携带冲突双方的 id。"""

    def __init__(self, plate: str, ids: list[int]):
        self.plate = plate
        self.ids = sorted(ids)
        super().__init__(f"车牌 {plate} 与启用车辆 #{'、#'.join(map(str, self.ids))} 重复")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def list_all(conn: sqlite3.Connection) -> list[dict]:
    return [dict(r) for r in conn.execute("SELECT * FROM vehicles ORDER BY id").fetchall()]


def get(conn: sqlite3.Connection, vehicle_id: int) -> dict | None:
    row = conn.execute("SELECT * FROM vehicles WHERE id=?", (vehicle_id,)).fetchone()
    return dict(row) if row else None


def get_active(conn: sqlite3.Connection, vehicle_id: int) -> dict | None:
    row = conn.execute(
        "SELECT * FROM vehicles WHERE id=? AND active=1", (vehicle_id,)
    ).fetchone()
    return dict(row) if row else None


def _active_ids_for_plate(conn: sqlite3.Connection, plate: str) -> list[int]:
    return [r["id"] for r in conn.execute(
        "SELECT id FROM vehicles WHERE plate=? AND active=1 ORDER BY id", (plate,)
    ).fetchall()]


def _reject_if_dup_active(conn: sqlite3.Connection, plate: str):
    ids = _active_ids_for_plate(conn, plate)
    if len(ids) >= 2:
        conn.rollback()
        raise VehicleConflict(plate, ids)


def _clean_plate(plate: str) -> str:
    plate = (plate or "").strip()
    if not plate:
        raise ValueError("车牌不能为空")
    return plate


def create(conn: sqlite3.Connection, plate: str, active: bool = True) -> dict:
    plate = _clean_plate(plate)
    cur = conn.execute(
        "INSERT INTO vehicles(plate,active,created_at) VALUES (?,?,?)",
        (plate, 1 if active else 0, _now()),
    )
    new_id = int(cur.lastrowid)
    if active:
        _reject_if_dup_active(conn, plate)
    conn.commit()
    return get(conn, new_id)


def update(conn: sqlite3.Connection, vehicle_id: int, plate: str | None = None, active: bool | None = None) -> dict | None:
    row = get(conn, vehicle_id)
    if not row:
        return None
    new_plate = row["plate"] if plate is None else _clean_plate(plate)
    new_active = bool(row["active"]) if active is None else active
    conn.execute(
        "UPDATE vehicles SET plate=?, active=? WHERE id=?",
        (new_plate, 1 if new_active else 0, vehicle_id),
    )
    if new_active:
        _reject_if_dup_active(conn, new_plate)
    conn.commit()
    return get(conn, vehicle_id)
