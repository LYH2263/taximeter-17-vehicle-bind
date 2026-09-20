from fastapi import APIRouter
from app.services.taxi_service import TaxiService
router = APIRouter()
@router.get("/history")
def history(limit: int = 50, plate: str | None = None):
    with TaxiService() as s: return {"items": s.history(limit, plate)}
