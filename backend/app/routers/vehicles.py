from fastapi import APIRouter, HTTPException
from app.schemas.vehicle import VehicleCreate, VehicleUpdate
from app.services.taxi_service import TaxiService, VehicleInvalid
from app.repositories.vehicles import VehicleConflict

router = APIRouter()


def _conflict(e: VehicleConflict) -> HTTPException:
    return HTTPException(status_code=409, detail=f"{e}（冲突车辆编号：{', '.join(map(str, e.ids))}）")


@router.get("/vehicles")
def list_vehicles():
    with TaxiService() as s:
        return {"items": s.list_vehicles()}


@router.post("/vehicles")
def create_vehicle(body: VehicleCreate):
    with TaxiService() as s:
        try:
            return s.create_vehicle(body.plate, body.active)
        except VehicleConflict as e:
            raise _conflict(e)
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))


@router.patch("/vehicles/{vehicle_id}")
def update_vehicle(vehicle_id: int, body: VehicleUpdate):
    with TaxiService() as s:
        try:
            return s.update_vehicle(vehicle_id, body.plate, body.active)
        except VehicleConflict as e:
            raise _conflict(e)
        except VehicleInvalid:
            raise HTTPException(status_code=404, detail=f"车辆 #{vehicle_id} 不存在")
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))
