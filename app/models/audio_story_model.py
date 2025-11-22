from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

# Audio story base model
class AudioStoryBase(BaseModel):
    channel_id: str
    meta_details: Optional[Dict] = None

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
class AudioStoryDB(BaseModel):
    channel_id: str
    file_path: str
    file_name: Optional[str] = None
    name: Optional[str] = None
    title: Optional[str] = None
    thumbnail: Optional[str] = None
    description: Optional[str] = None
    is_ready: Optional[bool] = False
    meta_details: Optional[Dict[str, Any]] = None

# Model for audio story list
class AudioStoryList(AudioStoryBase):
    id: str
    channel_id: str
    meta_details: Optional[Dict] = None

# Model for paginated response of audio stories
class PaginatedAudioResponse(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int
    channel_info: Optional[Dict[str, Any]] = None
    data: List[AudioStoryList]