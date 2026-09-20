from app.db import connect
from app.engines.night_compare import compare_day_night
from app.engines.tariff_breakdown import calc_fare
from app.repositories import runs, settings, tariff, trips, vehicles
from app.repositories.vehicles import VehicleConflict


class VehicleRequired(Exception):
    """落表未携带车辆编号。"""


class VehicleInvalid(Exception):
    """车辆不存在或已停用。"""


class TaxiService:
    def __init__(self): self._c = connect()
    def close(self): self._c.close()
    def __enter__(self): return self
    def __exit__(self, *a): self.close()
    def list_trips(self): return trips.list_all(self._c)
    def trip(self, tid): return trips.get(self._c, tid)
    def tariff(self): return tariff.get_active(self._c)
    def settings(self): return settings.get_map(self._c)
    def history(self, limit=50, plate=None): return runs.list_recent(self._c, limit, plate)

    def list_vehicles(self): return vehicles.list_all(self._c)
    def create_vehicle(self, plate, active=True):
        try:
            return vehicles.create(self._c, plate, active)
        except VehicleConflict:
            raise
    def update_vehicle(self, vehicle_id, plate=None, active=None):
        try:
            row = vehicles.update(self._c, vehicle_id, plate, active)
        except VehicleConflict:
            raise
        if not row:
            raise VehicleInvalid(f"车辆 #{vehicle_id} 不存在")
        return row

    def fare(self, distance_km, slow_min, night, trip_id, persist, vehicle_id=None):
        t = tariff.get_active(self._c)
        r = calc_fare(distance_km, slow_min, night, t)
        if not persist:
            # 只读试算：不校验车辆、不写记录，回包不含 run_id 与车牌
            return dict(r)
        if vehicle_id is None:
            raise VehicleRequired("落表必须指定一辆启用中的车辆")
        v = vehicles.get_active(self._c, vehicle_id)
        if not v:
            exists = vehicles.get(self._c, vehicle_id)
            if exists:
                raise VehicleInvalid(f"车辆 #{vehicle_id}（车牌 {exists['plate']}）已停用，不能落表")
            raise VehicleInvalid(f"车辆 #{vehicle_id} 不存在，不能落表")
        rid = runs.insert(self._c, "fare",
                          {"distance_km": distance_km, "slow_min": slow_min, "night": night},
                          r, trip_id, vehicle_id=v["id"], plate=v["plate"])
        return {"run_id": rid, "vehicle_id": v["id"], "plate": v["plate"], **r}

    def compare(self, distance_km, slow_min, persist):
        t = tariff.get_active(self._c)
        r = compare_day_night(distance_km, slow_min, t)
        rid = runs.insert(self._c, "compare", {"distance_km": distance_km, "slow_min": slow_min}, r, None) if persist else None
        return {"run_id": rid, **r}

    def dashboard(self):
        items = trips.list_all(self._c)
        clean = [x for x in items if "种子" not in x["label"]]
        dirty = [x for x in items if "种子" in x["label"]]
        return {"trip_count": len(items), "clean": len(clean), "dirty": len(dirty)}
