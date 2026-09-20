import sqlite3
import pytest
from fastapi import HTTPException
from app.seed import SCHEMA
from app.services.taxi_service import TaxiService

def make_service():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    conn.execute("INSERT INTO tariff(start_price,start_include_km,per_km,per_slow_min,night_factor) VALUES (11,3,2.5,0.8,1.2)")
    conn.commit()
    return TaxiService(conn)

def test_create_and_list_vehicles():
    with make_service() as s:
        v = s.create_vehicle("沪A12345", True)
        assert v["id"] and v["plate"] == "沪A12345" and v["enabled"] == 1
        assert [x["id"] for x in s.list_vehicles()] == [v["id"]]

def test_plate_empty_rejected():
    with make_service() as s:
        for bad in ("", "   "):
            with pytest.raises(HTTPException) as e:
                s.create_vehicle(bad, True)
            assert e.value.status_code == 400
        v = s.create_vehicle("沪A12345", True)
        with pytest.raises(HTTPException):
            s.update_vehicle(v["id"], "  ", True)

def test_duplicate_enabled_plate_rejected_names_both():
    with make_service() as s:
        a = s.create_vehicle("沪A12345", True)
        with pytest.raises(HTTPException) as e:
            s.create_vehicle("沪A12345", True)
        assert e.value.status_code == 400
        assert f"#{a['id']}" in e.value.detail and "新车辆" in e.value.detail

def test_disabled_may_share_plate_but_enabling_conflict_rejected():
    with make_service() as s:
        a = s.create_vehicle("沪A12345", True)
        b = s.create_vehicle("沪A12345", False)
        assert b["enabled"] == 0
        with pytest.raises(HTTPException) as e:
            s.update_vehicle(b["id"], "沪A12345", True)
        assert f"#{a['id']}" in e.value.detail and f"#{b['id']}" in e.value.detail

def test_update_and_disable_vehicle():
    with make_service() as s:
        a = s.create_vehicle("沪A12345", True)
        v = s.update_vehicle(a["id"], "沪B99999", True)
        assert v["plate"] == "沪B99999"
        v = s.disable_vehicle(a["id"])
        assert v["enabled"] == 0 and v["plate"] == "沪B99999"
        with pytest.raises(HTTPException) as e:
            s.disable_vehicle(999)
        assert e.value.status_code == 404

def test_fare_persist_without_vehicle_rejected_no_record():
    with make_service() as s:
        with pytest.raises(HTTPException) as e:
            s.fare(5, 2, False, None, True, None)
        assert e.value.status_code == 400
        assert s.history()["total"] == 0

def test_fare_persist_unknown_vehicle_rejected_no_record():
    with make_service() as s:
        with pytest.raises(HTTPException):
            s.fare(5, 2, False, None, True, 999)
        assert s.history()["total"] == 0

def test_fare_persist_disabled_vehicle_rejected_no_record():
    with make_service() as s:
        v = s.create_vehicle("沪A12345", False)
        with pytest.raises(HTTPException):
            s.fare(5, 2, False, None, True, v["id"])
        assert s.history()["total"] == 0

def test_fare_persist_writes_plate_snapshot():
    with make_service() as s:
        v = s.create_vehicle("沪A12345", True)
        r = s.fare(5, 2, False, None, True, v["id"])
        assert r["run_id"] and r["plate"] == "沪A12345"
        h = s.history()
        assert h["total"] == 1 and h["items"][0]["plate"] == "沪A12345"

def test_fare_readonly_no_vehicle_no_run_id_no_record():
    with make_service() as s:
        r = s.fare(5, 2, False, None, False, None)
        assert "run_id" not in r and "plate" not in r
        assert s.history()["total"] == 0

def test_records_keep_plate_after_rename_and_disable():
    with make_service() as s:
        v = s.create_vehicle("沪A12345", True)
        s.fare(5, 2, False, None, True, v["id"])
        s.update_vehicle(v["id"], "沪B99999", True)
        s.fare(6, 3, False, None, True, v["id"])
        s.disable_vehicle(v["id"])
        assert s.history()["total"] == 2
        a = s.history(plate="沪A12345")
        b = s.history(plate="沪B99999")
        assert a["total"] == 1 and a["items"][0]["plate"] == "沪A12345"
        assert b["total"] == 1 and b["items"][0]["plate"] == "沪B99999"

def test_history_plate_filter_count_matches_writes():
    with make_service() as s:
        v1 = s.create_vehicle("沪A12345", True)
        v2 = s.create_vehicle("沪B99999", True)
        for _ in range(3): s.fare(5, 2, False, None, True, v1["id"])
        s.fare(5, 2, False, None, True, v2["id"])
        assert s.history(plate="沪A12345")["total"] == 3
        assert s.history(plate="沪B99999")["total"] == 1
        assert s.history(plate="沪C00000")["total"] == 0

def test_compare_persist_needs_no_vehicle():
    with make_service() as s:
        r = s.compare(5, 2, True)
        assert r["run_id"]
        assert s.history()["total"] == 1
        assert s.history()["items"][0]["plate"] is None
