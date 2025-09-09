from pydantic import BaseModel
from uuid import UUID


# --- Role Management Models ---
class RoleBase(BaseModel):
    name: str

class RoleCreate(RoleBase):
    pass

class RoleUpdate(RoleBase):
    pass

class RoleInDB(RoleBase):
    id: UUID

    class Config:
        from_attributes = True