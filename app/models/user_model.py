# user_model.py
from typing import Optional, Dict, Any, List

from pydantic import BaseModel, EmailStr, constr

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

# Model for updating user favorite channel
class FavoriteChannel(BaseModel):
    channel_id: str

# Basic response
class UserResponse(BaseModel):
    status: bool = True
    detail: str

# Model for creating a playlist
class PlaylistCreate(BaseModel):
    name: constr(
        strip_whitespace=True,
        min_length=3,
        max_length=50,
        pattern=r"^[\w\s\-]+$"
    )
    videos: List

class PlaylistCreateResponse(UserResponse):
    playlist_id: str