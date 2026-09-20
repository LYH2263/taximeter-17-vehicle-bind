from fastapi import APIRouter
from app.schemas.fare import VehicleCreate, VehicleUpdate
from app.services.taxi_service import TaxiService
router = APIRouter()
@router.get("/vehicles")
def list_vehicles():
    with TaxiService() as s: return {"items": s.list_vehicles()}
@router.post("/vehicles")
def create_vehicle(body: VehicleCreate):
    with TaxiService() as s: return s.create_vehicle(body.plate, body.enabled)
@router.put("/vehicles/{vid}")
def update_vehicle(vid: int, body: VehicleUpdate):
    with TaxiService() as s: return s.update_vehicle(vid, body.plate, body.enabled)
@router.post("/vehicles/{vid}/disable")
def disable_vehicle(vid: int):
    with TaxiService() as s: return s.disable_vehicle(vid)
