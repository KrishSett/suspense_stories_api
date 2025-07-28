from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import FileResponse
from typing import List, Dict, Any
from auth.dependencies import JWTAuthGuard
from app.models import ChannelActiveList
from app.services import AdminService, UserService, ChannelService, AudioStoriesService
from common import RedisHashCache
from config import config
from utils.helpers import generate_signed_url, decode_signed_url_token
from jose import jwt, JWTError
import os


userRouter = APIRouter(prefix="/users", tags=["users"])

admin_service = AdminService()
user_service = UserService()
channel_service = ChannelService()
audio_stories_service = AudioStoriesService()
cache = RedisHashCache(prefix=config["cache_prefix"])

# Get list of active channels
@userRouter.get("/channels-list", response_model=List[ChannelActiveList])
async def get_channels(current_user: dict = Depends(JWTAuthGuard("user"))):
    try:
        channel_cursor = await channel_service.list_active_channels()

        if not channel_cursor:
            raise HTTPException(status_code=404, detail="No active channels found.")

        channels = []
        for ch in channel_cursor:
            channels.append({
                "channel_id": str(ch["_id"]),
                "youtube_channel_id": ch["youtube_channel_id"],
                "title": ch["title"],
                "is_active": ch.get("is_active", True),
                "order_position": ch["order_position"],
                "description": ch.get("description") or "No description available",
                "thumbnail_url": ch.get("thumbnail_url") or "https://example.com/default_thumbnail.png",
                "status": True
            })

        return channels
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Get list of stories by channel ID
@userRouter.get("/channels/{channel_id}/stories", response_model=List[Dict[str, Any]])
async def list_stories(channel_id: str, current_user: dict = Depends(JWTAuthGuard("user"))):
    stories = await audio_stories_service.get_audio_story_by_channel_id(channel_id)

    if not stories:
        raise HTTPException(status_code=404, detail="No stories found for this channel")

    return stories

# Get audio file path for a specific story
@userRouter.get("/stories-audio/{story_id}")
async def fetch_audio(story_id: str):
    story = await audio_stories_service.get_audio_story_by_id(story_id)
    if not story:
        raise HTTPException(status_code=404, detail="Audio story not found")

    signed_url = generate_signed_url(story["file_name"], expiry_seconds=86400)

    return {"signed_url": signed_url, "expires_in": 86400}

@userRouter.get("/audio-download/{filename}")
async def audio_download(filename: str, token: str = Query(...)):
    try:
        payload = decode_signed_url_token(token)

        if payload.get("filename") != filename:
            raise HTTPException(status_code=403, detail="Invalid token")

        if not filename.endswith('.m4a'):
            raise HTTPException(status_code=400, detail="Invalid file type. Only .m4a files are allowed.")
    except JWTError:
        raise HTTPException(status_code=403, detail="Invalid token")

    file_path = os.path.join('downloads', filename)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(file_path, media_type="audio/mpeg")