from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from .base_model import MongoBaseModel, PyObjectId

# Input model for creating
class AudioStoryCreate(BaseModel):
    channel_id: str
    file_path: str

# Response after creation
class AudioStoryQueuedResponse(BaseModel):
    story_id: str
    file_name: str
    status: str = "queued"

# Full DB model base
class AudioStoryDB(MongoBaseModel):
    channel_id: str
    file_path: str
    file_name: Optional[str] = None
    name: Optional[str] = None
    title: Optional[str] = None
    thumbnail: Optional[str] = None
    description: Optional[str] = None
    is_ready: Optional[bool] = False
    meta_details: Optional[Dict[str, Any]] = None

# For listing
class AudioStoryList(AudioStoryDB):
    id: PyObjectId = Field(alias="_id")
