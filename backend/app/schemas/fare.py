from pydantic import BaseModel, Field

class FareRequest(BaseModel):
    distance_km: float = Field(ge=0)
    slow_min: float = Field(ge=0)
    night: bool = False
    trip_id: int | None = None
    persist: bool = True
    vehicle_id: int | None = None

class CompareRequest(BaseModel):
    distance_km: float = Field(ge=0)
    slow_min: float = Field(ge=0)
    persist: bool = False

class VehicleCreate(BaseModel):
    plate: str = ""
    enabled: bool = True

class VehicleUpdate(BaseModel):
    plate: str = ""
    enabled: bool = True
