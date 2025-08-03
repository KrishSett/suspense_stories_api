# channel_model.py
from pydantic import BaseModel, constr
from typing import Optional, List
from datetime import datetime

# Base model for shared fields
class ChannelBase(BaseModel):
    youtube_channel_id: str
    title: str
    description: Optional[constr(min_length=10, max_length=500)]
    thumbnail_url: Optional[constr(pattern=r"^https?://[^\s]+$", min_length=5, max_length=500)]
    order_position: int

# Model for creating a channel
class ChannelCreate(ChannelBase):
    is_active: Optional[bool] = True
    published_at: Optional[datetime] = None
    created_by: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

# Model for viewing a channel
class ChannelView(ChannelBase):
    channel_id: str
    is_active: bool = True

# Model for updating a channel
class ChannelUpdate(BaseModel):
    channel_id: str
    description: Optional[constr(min_length=10, max_length=500)]
    thumbnail_url: Optional[constr(pattern=r"^https?://[^\s]+$", min_length=5, max_length=500)]

# Model for returning a channel in response
class ChannelList(BaseModel):
    channel_id: str
    status: bool = True

# Model for active channel list
class ChannelActiveList(ChannelBase):
    channel_id: str

# Basic response
class ChannelResponse(BaseModel):
    status: bool = True
    detail: str

# Model for returning a channel in response
class ChannelSetOrder(BaseModel):
    channel_id: str
    order_position: int

# Model for paginated response of channels
class PaginatedChannelsResponse(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int
    data: List[ChannelActiveList]