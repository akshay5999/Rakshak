from pydantic import BaseModel
from typing import Optional


class SoldierBase(BaseModel):
    service_number: str
    name: str
    rank: str
    unit: str
    location: Optional[str] = None
    phone: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    is_active: bool = True
    stress_level: float = 0.0


class SoldierCreate(SoldierBase):
    pass


class SoldierResponse(SoldierBase):
    id: int

    class Config:
        from_attributes = True