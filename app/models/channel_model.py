# channel_model.py
from pydantic import Field, HttpUrl
from typing import Optional
from datetime import datetime
from .base_model import MongoBaseModel, PyObjectId

# Base model for shared fields
class ChannelBase(MongoBaseModel):
    youtube_channel_id: str
    title: str
    description: Optional[str] = None
    thumbnail_url: Optional[HttpUrl] = None
    published_at: Optional[datetime] = None
    order_position: int
    is_active: Optional[bool] = True

# Model for creating a channel
class ChannelCreate(ChannelBase):
    created_by: Optional[str] = None

# Model for updating a channel
class ChannelUpdate(MongoBaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    thumbnail_url: Optional[HttpUrl] = None
    order_position: Optional[int] = None
    is_active: Optional[bool] = None

# Model for returning a channel in response
class ChannelList(ChannelBase):
    _id: str

