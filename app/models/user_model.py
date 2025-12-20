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

# Model for updating an existing playlist contents
class PlaylistContentUpdate(BaseModel):
    video_id: str

# Playlist create response model
class PlaylistCreateResponse(UserResponse):
    playlist_id: str

# User profile model
class UserProfileResponse(UserBase):
    phone: Optional[constr(min_length=10, max_length=15)] = None
    is_active: bool = True
    profile_img: str
    type: str

# Model for user profile update
class UserProfileUpdate(BaseModel):
    firstname: Optional[constr(
        strip_whitespace=True,
        min_length=1,
        max_length=50,
        pattern=r'^[A-Za-z ]+$'
    )] = None
    lastname: Optional[constr(
        strip_whitespace=True,
        min_length=1,
        max_length=50,
        pattern=r'^[A-Za-z ]+$'
    )] = None
    phone: Optional[constr(
        min_length=10,
        max_length=15,
        pattern=r'^\+?\d+$'
    )] = None

# Model for sign-out response
class SignOutResponse(BaseModel):
    status: bool
    detail: str

# Model for playlist contents
class PlaylistContentsResponse(BaseModel):
    playlist_id: str
    name: str
    playlist_items: List[Dict[str, Any]]