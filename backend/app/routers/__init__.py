from fastapi import APIRouter
from app.routers import dashboard, fare, history, settings, tariff, trips, vehicles

api = APIRouter(prefix="/api")
for r in (dashboard, trips, tariff, fare, history, settings, vehicles):
    api.include_router(r.router)
