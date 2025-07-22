# audio_story_model.py
from pydantic import Field
from typing import Optional
from .base_model import MongoBaseModel, PyObjectId

# Base model for audio story
class AudioStoryBase(MongoBaseModel):
    name: str
    channel_id: str
    thumbnail: str
    description: str
    title: str
    file_name: str
    file_path: Optional[str] = None
    is_ready: Optional[bool] = False

# Model for creating audio story
class AudioStoryCreate(AudioStoryBase):
    pass

# Model for updating audio story
class AudioStoryUpdate(MongoBaseModel):
    name: Optional[str] = None
    channel_id: Optional[str] = None
    thumbnail: Optional[str] = None
    description: Optional[str] = None
    title: Optional[str] = None
    file_name: Optional[str] = None
    file_path: Optional[str] = None
    is_ready: Optional[bool] = None

# Model for listing audio story
class AudioStoryList(AudioStoryBase):
    id: PyObjectId = Field(alias="_id")
