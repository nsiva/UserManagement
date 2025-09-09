from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime


# --- Firm Management Models ---
class FirmBase(BaseModel):
    company_name: str
    address_1: Optional[str] = None
    address_2: Optional[str] = None
    city_town: Optional[str] = None
    state: Optional[str] = None
    zip: Optional[str] = None
    country: Optional[str] = None
    email: Optional[str] = None
    phone_number: Optional[str] = None

class FirmCreate(FirmBase):
    pass

class FirmUpdate(BaseModel):
    company_name: Optional[str] = None
    address_1: Optional[str] = None
    address_2: Optional[str] = None
    city_town: Optional[str] = None
    state: Optional[str] = None
    zip: Optional[str] = None
    country: Optional[str] = None
    email: Optional[str] = None
    phone_number: Optional[str] = None

class FirmInDB(FirmBase):
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class FirmResponse(FirmBase):
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True