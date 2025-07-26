from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
from auth.dependencies import JWTAuthGuard

userRouter = APIRouter(
    prefix="/users",
    tags=['users']
)

# Dummy data for demonstration
channels = [
    {"id": 1, "name": "Tech"},
    {"id": 2, "name": "Music"},
]

stories = [
    {"id": 101, "channel_id": 1, "title": "AI Revolution", "audio_id": 1001},
    {"id": 102, "channel_id": 2, "title": "Jazz Classics", "audio_id": 1002},
]

audio_files = {
    1001: {"url": "/audio/1001.mp3", "duration": 300, "bitrate": "320kbps"},
    1002: {"url": "/audio/1002.mp3", "duration": 180, "bitrate": "256kbps"},
}

@userRouter.get("/channels-list", response_model=List[Dict[str, Any]])
def get_channels(current_user: dict = Depends(JWTAuthGuard("user"))):
    return channels

@userRouter.get("/channels/{channel_id}", response_model=Dict[str, Any])
def view_channel(channel_id: int, current_user: dict = Depends(JWTAuthGuard("user"))):
    for channel in channels:
        if channel["id"] == channel_id:
            return channel
    raise HTTPException(status_code=404, detail="Channel not found")

@userRouter.get("/channels/{channel_id}/stories", response_model=List[Dict[str, Any]])
def list_stories(channel_id: int, current_user: dict = Depends(JWTAuthGuard("user"))):
    return [story for story in stories if story["channel_id"] == channel_id]

@userRouter.get("/stories/{story_id}/audio", response_model=Dict[str, Any])
def fetch_audio(story_id: int, current_user: dict = Depends(JWTAuthGuard("user"))):
    for story in stories:
        if story["id"] == story_id:
            audio_id = story["audio_id"]
            if audio_id in audio_files:
                return audio_files[audio_id]
            raise HTTPException(status_code=404, detail="Audio not found")
    raise HTTPException(status_code=404, detail="Story not found")