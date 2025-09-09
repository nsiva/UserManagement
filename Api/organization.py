from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime


# --- Organization Management Models ---
class OrganizationBase(BaseModel):
    company_name: str
    address_1: Optional[str] = None
    address_2: Optional[str] = None
    city_town: Optional[str] = None
    state: Optional[str] = None
    zip: Optional[str] = None
    country: Optional[str] = None
    email: Optional[str] = None
    phone_number: Optional[str] = None

class OrganizationCreate(OrganizationBase):
    pass

class OrganizationUpdate(BaseModel):
    company_name: Optional[str] = None
    address_1: Optional[str] = None
    address_2: Optional[str] = None
    city_town: Optional[str] = None
    state: Optional[str] = None
    zip: Optional[str] = None
    country: Optional[str] = None
    email: Optional[str] = None
    phone_number: Optional[str] = None

class OrganizationInDB(OrganizationBase):
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class OrganizationResponse(OrganizationBase):
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True