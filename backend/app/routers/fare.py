from fastapi import APIRouter, HTTPException
from app.schemas.fare import CompareRequest, FareRequest
from app.services.taxi_service import TaxiService, VehicleInvalid, VehicleRequired
router = APIRouter()
@router.post("/fare")
def post_fare(body: FareRequest):
    with TaxiService() as s:
        try:
            return s.fare(body.distance_km, body.slow_min, body.night, body.trip_id, body.persist, body.vehicle_id)
        except VehicleRequired as e:
            raise HTTPException(status_code=400, detail=str(e))
        except VehicleInvalid as e:
            raise HTTPException(status_code=422, detail=str(e))
@router.post("/compare")
def post_compare(body: CompareRequest):
    with TaxiService() as s:
        return s.compare(body.distance_km, body.slow_min, body.persist)
