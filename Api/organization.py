from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from uuid import UUID
from datetime import datetime


# --- Organization Management Models ---
class OrganizationBase(BaseModel):
    company_name: str = Field(..., min_length=2, max_length=255, description="Company or organization name")
    address_1: str = Field(..., max_length=255, description="Primary address line")
    address_2: Optional[str] = Field(None, max_length=255, description="Secondary address line (optional)")
    city_town: str = Field(..., min_length=2, max_length=100, description="City or town")
    state: str = Field(..., min_length=2, max_length=100, description="State or province")
    zip: str = Field(..., min_length=3, max_length=20, description="ZIP or postal code")
    country: str = Field(..., min_length=2, max_length=100, description="Country")
    email: EmailStr = Field(..., max_length=255, description="Contact email address")
    phone_number: str = Field(..., min_length=7, max_length=50, description="Contact phone number")
    
    @validator('company_name', 'state', 'country')
    def validate_text_fields(cls, v):
        if v:
            v = v.strip()
            if len(v) < 2:
                raise ValueError('Must be at least 2 characters long')
        return v
    
    @validator('address_1', 'address_2', 'city_town')
    def validate_address_fields(cls, v):
        if v:
            v = v.strip()
        return v
    
    @validator('phone_number')
    def validate_phone(cls, v):
        import re
        if v:
            v = v.strip()
            # Basic phone validation - allows international formats
            phone_pattern = re.compile(r'^[\+]?[1-9][\d\s\-\(\)]{6,18}$')
            if not phone_pattern.match(v):
                raise ValueError('Invalid phone number format')
        return v
    
    @validator('zip')
    def validate_zip(cls, v):
        if v:
            v = v.strip()
            if len(v) < 3:
                raise ValueError('ZIP code must be at least 3 characters')
        return v

class OrganizationCreate(OrganizationBase):
    pass

class OrganizationUpdate(BaseModel):
    company_name: Optional[str] = Field(None, min_length=2, max_length=255, description="Company or organization name")
    address_1: Optional[str] = Field(None, max_length=255, description="Primary address line")
    address_2: Optional[str] = Field(None, max_length=255, description="Secondary address line")
    city_town: Optional[str] = Field(None, min_length=2, max_length=100, description="City or town")
    state: Optional[str] = Field(None, min_length=2, max_length=100, description="State or province")
    zip: Optional[str] = Field(None, min_length=3, max_length=20, description="ZIP or postal code")
    country: Optional[str] = Field(None, min_length=2, max_length=100, description="Country")
    email: Optional[EmailStr] = Field(None, max_length=255, description="Contact email address")
    phone_number: Optional[str] = Field(None, min_length=7, max_length=50, description="Contact phone number")
    
    @validator('company_name', 'state', 'country')
    def validate_text_fields(cls, v):
        if v:
            v = v.strip()
            if len(v) < 2:
                raise ValueError('Must be at least 2 characters long')
        return v
    
    @validator('address_1', 'address_2', 'city_town')
    def validate_address_fields(cls, v):
        if v:
            v = v.strip()
        return v
    
    @validator('phone_number')
    def validate_phone(cls, v):
        import re
        if v:
            v = v.strip()
            # Basic phone validation - allows international formats
            phone_pattern = re.compile(r'^[\+]?[1-9][\d\s\-\(\)]{6,18}$')
            if not phone_pattern.match(v):
                raise ValueError('Invalid phone number format')
        return v
    
    @validator('zip')
    def validate_zip(cls, v):
        if v:
            v = v.strip()
            if len(v) < 3:
                raise ValueError('ZIP code must be at least 3 characters')
        return v

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
    business_units_count: int = 0
    users_count: int = 0

    class Config:
        from_attributes = True