from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from uuid import UUID
from datetime import datetime


# --- Business Unit Management Models ---
class BusinessUnitBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=255, description="Business unit name")
    description: Optional[str] = Field(None, max_length=1000, description="Business unit description")
    code: Optional[str] = Field(None, min_length=2, max_length=50, description="Internal reference code")
    organization_id: UUID = Field(..., description="Organization this unit belongs to")
    parent_unit_id: Optional[UUID] = Field(None, description="Parent business unit for hierarchy")
    manager_id: Optional[UUID] = Field(None, description="User who manages this unit")
    location: Optional[str] = Field(None, max_length=255, description="Physical location")
    country: Optional[str] = Field(None, max_length=100, description="Operating country")
    region: Optional[str] = Field(None, max_length=100, description="Operating region")
    email: Optional[EmailStr] = Field(None, max_length=255, description="Contact email")
    phone_number: Optional[str] = Field(None, max_length=50, description="Contact phone number")
    is_active: bool = Field(True, description="Whether the unit is active")
    
    @validator('name')
    def validate_name(cls, v):
        if v:
            v = v.strip()
            if len(v) < 2:
                raise ValueError('Business unit name must be at least 2 characters long')
        return v
    
    @validator('code')
    def validate_code(cls, v):
        if v:
            v = v.strip().upper()
            import re
            # Code should be alphanumeric with underscores and hyphens
            if not re.match(r'^[A-Z0-9_-]+$', v):
                raise ValueError('Code must contain only uppercase letters, numbers, underscores, and hyphens')
            if len(v) < 2:
                raise ValueError('Code must be at least 2 characters long')
        return v
    
    @validator('description', 'location')
    def validate_optional_text(cls, v):
        if v:
            v = v.strip()
            if len(v) == 0:
                return None
        return v
    
    @validator('country', 'region')
    def validate_location_fields(cls, v):
        if v:
            v = v.strip().title()
            if len(v) < 2:
                raise ValueError('Must be at least 2 characters long')
        return v
    
    @validator('phone_number')
    def validate_phone(cls, v):
        if v:
            v = v.strip()
            import re
            # Basic international phone validation
            phone_pattern = re.compile(r'^[\+]?[1-9][\d\s\-\(\)]{6,18}$')
            if not phone_pattern.match(v):
                raise ValueError('Invalid phone number format')
        return v
    
    @validator('parent_unit_id')
    def validate_parent_unit(cls, v, values):
        # Note: We can't validate organizational consistency here as we don't have DB access
        # This will be handled in the API layer
        return v


class BusinessUnitCreate(BusinessUnitBase):
    created_by: Optional[UUID] = Field(None, description="User creating this record")


class BusinessUnitUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255, description="Business unit name")
    description: Optional[str] = Field(None, max_length=1000, description="Business unit description")
    code: Optional[str] = Field(None, min_length=2, max_length=50, description="Internal reference code")
    parent_unit_id: Optional[UUID] = Field(None, description="Parent business unit for hierarchy")
    manager_id: Optional[UUID] = Field(None, description="User who manages this unit")
    location: Optional[str] = Field(None, max_length=255, description="Physical location")
    country: Optional[str] = Field(None, max_length=100, description="Operating country")
    region: Optional[str] = Field(None, max_length=100, description="Operating region")
    email: Optional[EmailStr] = Field(None, max_length=255, description="Contact email")
    phone_number: Optional[str] = Field(None, max_length=50, description="Contact phone number")
    is_active: Optional[bool] = Field(None, description="Whether the unit is active")
    updated_by: Optional[UUID] = Field(None, description="User updating this record")
    
    @validator('name')
    def validate_name(cls, v):
        if v:
            v = v.strip()
            if len(v) < 2:
                raise ValueError('Business unit name must be at least 2 characters long')
        return v
    
    @validator('code')
    def validate_code(cls, v):
        if v:
            v = v.strip().upper()
            import re
            if not re.match(r'^[A-Z0-9_-]+$', v):
                raise ValueError('Code must contain only uppercase letters, numbers, underscores, and hyphens')
            if len(v) < 2:
                raise ValueError('Code must be at least 2 characters long')
        return v
    
    @validator('description', 'location')
    def validate_optional_text(cls, v):
        if v:
            v = v.strip()
            if len(v) == 0:
                return None
        return v
    
    @validator('country', 'region')
    def validate_location_fields(cls, v):
        if v:
            v = v.strip().title()
            if len(v) < 2:
                raise ValueError('Must be at least 2 characters long')
        return v
    
    @validator('phone_number')
    def validate_phone(cls, v):
        if v:
            v = v.strip()
            import re
            phone_pattern = re.compile(r'^[\+]?[1-9][\d\s\-\(\)]{6,18}$')
            if not phone_pattern.match(v):
                raise ValueError('Invalid phone number format')
        return v


class BusinessUnitInDB(BusinessUnitBase):
    id: UUID
    created_at: datetime
    created_by: Optional[UUID] = None
    updated_at: Optional[datetime] = None
    updated_by: Optional[UUID] = None

    class Config:
        from_attributes = True


class BusinessUnitResponse(BusinessUnitBase):
    id: UUID
    created_at: datetime
    created_by: Optional[UUID] = None
    updated_at: Optional[datetime] = None
    updated_by: Optional[UUID] = None
    
    # Extended fields from joins
    organization_name: Optional[str] = Field(None, description="Organization name")
    parent_name: Optional[str] = Field(None, description="Parent unit name") 
    manager_name: Optional[str] = Field(None, description="Manager full name")

    class Config:
        from_attributes = True


class BusinessUnitHierarchy(BusinessUnitResponse):
    """Extended response model that includes hierarchy information"""
    children: Optional[list['BusinessUnitHierarchy']] = Field(None, description="Child business units")
    parent_name: Optional[str] = Field(None, description="Parent unit name")
    manager_name: Optional[str] = Field(None, description="Manager full name")
    organization_name: Optional[str] = Field(None, description="Organization name")


# Enable forward references for recursive model
BusinessUnitHierarchy.model_rebuild()


class BusinessUnitListResponse(BaseModel):
    """Response model for list operations with metadata"""
    business_units: list[BusinessUnitResponse]
    total_count: int
    organization_id: Optional[UUID] = None
    organization_name: Optional[str] = None