from pydantic import BaseModel, Field, field_validator


class VehicleCreate(BaseModel):
    plate: str = Field(min_length=1)
    active: bool = True

    @field_validator("plate")
    @classmethod
    def _strip_plate(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("车牌不能为空")
        return v


class VehicleUpdate(BaseModel):
    plate: str | None = Field(default=None, min_length=1)
    active: bool | None = None

    @field_validator("plate")
    @classmethod
    def _strip_plate(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = v.strip()
        if not v:
            raise ValueError("车牌不能为空")
        return v
