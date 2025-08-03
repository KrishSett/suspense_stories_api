# user_model.py
from typing import Optional, Dict, Any, List

from pydantic import BaseModel, EmailStr

# Base user model
class UserBase(BaseModel):
    firstname: str
    lastname: str
    email: EmailStr

# User list  model
class UserList(UserBase):
    is_active: bool = True

# Model for paginated response of users
class PaginatedUserResponse(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int
    channel: Optional[Dict[str, Any]] = None
    data: List[UserList]