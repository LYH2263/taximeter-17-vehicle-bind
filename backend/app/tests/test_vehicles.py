import os
import tempfile
import unittest

# 在导入 app.config 前指定独立数据目录，避免污染开发库
_tmp = tempfile.mkdtemp(prefix="taxitest-")
os.environ["DATA_DIR"] = _tmp

from app import seed
from app.db import connect
from app.services.taxi_service import TaxiService, VehicleInvalid, VehicleRequired
from app.repositories import vehicles as vehicles_repo
from app.repositories.vehicles import VehicleConflict

seed.init_db()


class VehicleBindingTests(unittest.TestCase):
    def setUp(self):
        self._conn = connect()
        self._conn.execute("DELETE FROM calc_runs")
        self._conn.execute("DELETE FROM vehicles")
        self._conn.commit()
        self._conn.close()
        self.service = TaxiService()
        self.plate_a = "测A0001"
        self.plate_b = "测B0002"

    def tearDown(self):
        self.service.close()

    # —— 车辆维护 ——

    def test_create_list_update_deactivate(self):
        v = self.service.create_vehicle(self.plate_a, True)
        self.assertTrue(v["active"])
        self.assertEqual(v["plate"], self.plate_a)
        self.assertIn(self.plate_a, [x["plate"] for x in self.service.list_vehicles()])
        v2 = self.service.update_vehicle(v["id"], plate=self.plate_b, active=True)
        self.assertEqual(v2["plate"], self.plate_b)
        v3 = self.service.update_vehicle(v["id"], active=False)
        self.assertFalse(v3["active"])

    def test_empty_plate_rejected(self):
        for bad in ("", "   "):
            with self.assertRaises(ValueError):
                vehicles_repo.create(connect(), bad, True)
        with self.assertRaises(ValueError):
            vid = self.service.create_vehicle("占位牌", True)["id"]
            self.service.update_vehicle(vid, plate="  ")

    def test_duplicate_active_plate_names_both_and_rolls_back(self):
        v1 = self.service.create_vehicle(self.plate_a, True)
        before = len(self.service.history(limit=10000))
        with self.assertRaises(VehicleConflict) as cm:
            self.service.create_vehicle(self.plate_a, True)
        # 点名两条：已存在的 v1 与本次尝试插入的新行
        self.assertIn(v1["id"], cm.exception.ids)
        self.assertEqual(len(cm.exception.ids), 2)
        active_same = [v for v in self.service.list_vehicles()
                       if v["plate"] == self.plate_a and v["active"]]
        self.assertEqual(len(active_same), 1)  # 冲突新行已回滚
        self.assertEqual(len(self.service.history(limit=10000)), before)

    def test_conflict_when_activating_second_names_both(self):
        v1 = self.service.create_vehicle(self.plate_a, True)
        v2 = self.service.create_vehicle(self.plate_a, False)  # 停用态允许同牌
        with self.assertRaises(VehicleConflict) as cm:
            self.service.update_vehicle(v2["id"], active=True)
        self.assertEqual(cm.exception.ids, [v1["id"], v2["id"]])  # 点名两条
        again = next(v for v in self.service.list_vehicles() if v["id"] == v2["id"])
        self.assertFalse(again["active"])  # 回滚后仍停用

    def test_plate_reusable_after_deactivate(self):
        v1 = self.service.create_vehicle(self.plate_a, True)
        self.service.update_vehicle(v1["id"], active=False)
        v2 = self.service.create_vehicle(self.plate_a, True)
        self.assertTrue(v2["active"])

    # —— 落表车辆绑定 ——

    def test_persist_without_vehicle_rejected_no_run(self):
        before = len(self.service.history(limit=10000))
        with self.assertRaises(VehicleRequired):
            self.service.fare(8, 3, False, None, True, vehicle_id=None)
        self.assertEqual(len(self.service.history(limit=10000)), before)

    def test_persist_unknown_vehicle_rejected_no_run(self):
        before = len(self.service.history(limit=10000))
        with self.assertRaises(VehicleInvalid):
            self.service.fare(8, 3, False, None, True, vehicle_id=999999)
        self.assertEqual(len(self.service.history(limit=10000)), before)

    def test_persist_disabled_vehicle_rejected_no_run(self):
        v = self.service.create_vehicle(self.plate_a, True)
        self.service.update_vehicle(v["id"], active=False)
        before = len(self.service.history(limit=10000))
        with self.assertRaises(VehicleInvalid):
            self.service.fare(8, 3, False, None, True, vehicle_id=v["id"])
        self.assertEqual(len(self.service.history(limit=10000)), before)

    def test_persist_writes_vehicle_id_and_plate_snapshot(self):
        v = self.service.create_vehicle(self.plate_a, True)
        out = self.service.fare(8, 3, False, None, True, vehicle_id=v["id"])
        self.assertIsNotNone(out["run_id"])
        self.assertEqual(out["plate"], self.plate_a)
        self.assertEqual(out["vehicle_id"], v["id"])
        row = next(r for r in self.service.history(limit=10000) if r["id"] == out["run_id"])
        self.assertEqual(row["vehicle_id"], v["id"])
        self.assertEqual(row["plate"], self.plate_a)

    def test_readonly_fare_no_identity_no_run(self):
        before = len(self.service.history(limit=10000))
        out = self.service.fare(8, 3, False, None, False, vehicle_id=None)
        self.assertNotIn("run_id", out)
        self.assertNotIn("plate", out)
        self.assertNotIn("vehicle_id", out)
        self.assertIn("total", out)
        self.assertEqual(len(self.service.history(limit=10000)), before)

    def test_history_keeps_plate_after_rename(self):
        v = self.service.create_vehicle(self.plate_a, True)
        rid = self.service.fare(8, 3, False, None, True, vehicle_id=v["id"])["run_id"]
        self.service.update_vehicle(v["id"], plate="改名后999")
        row = next(r for r in self.service.history(limit=10000) if r["id"] == rid)
        self.assertEqual(row["plate"], self.plate_a)

    def test_history_keeps_plate_after_disable(self):
        v = self.service.create_vehicle(self.plate_a, True)
        rid = self.service.fare(8, 3, False, None, True, vehicle_id=v["id"])["run_id"]
        self.service.update_vehicle(v["id"], active=False)
        row = next(r for r in self.service.history(limit=10000) if r["id"] == rid)
        self.assertEqual(row["plate"], self.plate_a)

    def test_history_filter_count_matches_written(self):
        v_a = self.service.create_vehicle(self.plate_a, True)
        v_b = self.service.create_vehicle(self.plate_b, True)
        n_a, n_b = 3, 2
        for _ in range(n_a):
            self.service.fare(5, 1, False, None, True, vehicle_id=v_a["id"])
        for _ in range(n_b):
            self.service.fare(5, 1, False, None, True, vehicle_id=v_b["id"])
        rows_a = self.service.history(limit=10000, plate=self.plate_a)
        rows_b = self.service.history(limit=10000, plate=self.plate_b)
        self.assertEqual(len(rows_a), n_a)
        self.assertEqual(len(rows_b), n_b)
        all_a = [r for r in self.service.history(limit=10000) if r["plate"] == self.plate_a]
        self.assertEqual(len(rows_a), len(all_a))
        # 改名后旧记录仍按旧牌命中，新牌查不到旧记录
        self.service.update_vehicle(v_b["id"], plate="改名后BB")
        self.assertEqual(len(self.service.history(limit=10000, plate=self.plate_b)), n_b)
        self.assertEqual(len(self.service.history(limit=10000, plate="改名后BB")), 0)

    def test_compare_persists_without_vehicle(self):
        before = len(self.service.history(limit=10000))
        out = self.service.compare(18, 12, True)
        self.assertIsNotNone(out["run_id"])
        self.assertEqual(len(self.service.history(limit=10000)), before + 1)
        row = next(r for r in self.service.history(limit=10000) if r["id"] == out["run_id"])
        self.assertEqual(row["kind"], "compare")
        self.assertIsNone(row["vehicle_id"])
        self.assertIsNone(row["plate"])


if __name__ == "__main__":
    unittest.main()
