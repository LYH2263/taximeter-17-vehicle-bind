from fastapi import HTTPException
from app.db import connect
from app.engines.night_compare import compare_day_night
from app.engines.tariff_breakdown import calc_fare
from app.repositories import runs, settings, tariff, trips, vehicles

class TaxiService:
    def __init__(self, conn=None): self._c = conn or connect()
    def close(self): self._c.close()
    def __enter__(self): return self
    def __exit__(self, *a): self.close()
    def list_trips(self): return trips.list_all(self._c)
    def trip(self, tid): return trips.get(self._c, tid)
    def tariff(self): return tariff.get_active(self._c)
    def settings(self): return settings.get_map(self._c)
    def history(self, limit=50, plate=None):
        plate = (plate or "").strip() or None
        return {"items": runs.list_recent(self._c, limit, plate), "total": runs.count(self._c, plate)}
    def fare(self, distance_km, slow_min, night, trip_id, persist, vehicle_id=None):
        t = tariff.get_active(self._c)
        r = calc_fare(distance_km, slow_min, night, t)
        if not persist:
            return r
        v = self._require_vehicle(vehicle_id)
        payload = {"distance_km": distance_km, "slow_min": slow_min, "night": night, "vehicle_id": v["id"]}
        rid = runs.insert(self._c, "fare", payload, r, trip_id, plate=v["plate"])
        return {"run_id": rid, "vehicle_id": v["id"], "plate": v["plate"], **r}
    def _require_vehicle(self, vehicle_id):
        if vehicle_id is None:
            raise HTTPException(400, "落表必须选择一条启用中的车辆")
        v = vehicles.get(self._c, vehicle_id)
        if not v:
            raise HTTPException(400, f"车辆 #{vehicle_id} 不存在，落表被拒绝")
        if not v["enabled"]:
            raise HTTPException(400, f"车辆 #{v['id']}（{v['plate']}）已停用，落表被拒绝")
        return v
    def compare(self, distance_km, slow_min, persist):
        t = tariff.get_active(self._c)
        r = compare_day_night(distance_km, slow_min, t)
        rid = runs.insert(self._c, "compare", {"distance_km": distance_km, "slow_min": slow_min}, r, None) if persist else None
        return {"run_id": rid, **r}
    def list_vehicles(self): return vehicles.list_all(self._c)
    def create_vehicle(self, plate, enabled=True):
        plate = self._clean_plate(plate)
        if enabled:
            other = vehicles.find_enabled_by_plate(self._c, plate)
            if other:
                raise HTTPException(400, f"车牌「{plate}」冲突：新车辆与车辆 #{other['id']} 均启用且车牌相同，已拒绝")
        return vehicles.create(self._c, plate, enabled)
    def update_vehicle(self, vid, plate, enabled):
        if not vehicles.get(self._c, vid):
            raise HTTPException(404, f"车辆 #{vid} 不存在")
        plate = self._clean_plate(plate)
        if enabled:
            other = vehicles.find_enabled_by_plate(self._c, plate, exclude_id=vid)
            if other:
                raise HTTPException(400, f"车牌「{plate}」冲突：车辆 #{vid} 与车辆 #{other['id']} 均启用且车牌相同，已拒绝")
        return vehicles.update(self._c, vid, plate, enabled)
    def disable_vehicle(self, vid):
        v = vehicles.get(self._c, vid)
        if not v:
            raise HTTPException(404, f"车辆 #{vid} 不存在")
        return vehicles.update(self._c, vid, v["plate"], False)
    @staticmethod
    def _clean_plate(plate):
        plate = (plate or "").strip()
        if not plate:
            raise HTTPException(400, "车牌不能为空")
        return plate
    def dashboard(self):
        items = trips.list_all(self._c)
        clean = [x for x in items if "种子" not in x["label"]]
        dirty = [x for x in items if "种子" in x["label"]]
        return {"trip_count": len(items), "clean": len(clean), "dirty": len(dirty)}
