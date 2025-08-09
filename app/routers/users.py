# users.py
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import FileResponse
from typing import List, Dict, Any
from auth.dependencies import JWTAuthGuard
from app.models import PlaylistCreate, PlaylistCreateResponse, PaginatedAudioResponse, PaginatedChannelsResponse, FavoriteChannel, UserResponse
from app.services import AdminService, UserService, ChannelService, AudioStoriesService
from common import RedisHashCache
from config import config
from utils.helpers import generate_signed_url, decode_signed_url_token, process_cache_key, generate_unique_id
from jose import jwt, JWTError
from bson import ObjectId, errors as bson_errors
import os

userRouter = APIRouter(prefix="/users", tags=["users"])
admin_service = AdminService()
user_service = UserService()
channel_service = ChannelService()
audio_stories_service = AudioStoriesService()
cache = RedisHashCache(prefix=config["cache_prefix"])

# Get list of active channels
@userRouter.get("/channels-list", response_model=PaginatedChannelsResponse)
async def get_channels(
        page: int = Query(1, ge=1, le=1000, description="Page number for pagination"),
        page_size: int = Query(10, ge=1, le=100, description="Number of channels per page"),
        current_user: dict = Depends(JWTAuthGuard("user"))
):
    try:
        cache_key = process_cache_key()

        # Check cache
        cached_channels = await cache.h_get(cache_key, "list_active_channels")
        if cached_channels is not None:
            return cached_channels

        channels = await channel_service.list_active_channels(page=page, page_size=page_size)

        if not channels:
            raise HTTPException(status_code=404, detail="No active channels found.")
        # Paginated response
        await cache.h_set(cache_key, "list_active_channels", channels, {"page": page, "page_size": page_size})
        return channels
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Get list of stories by channel ID
@userRouter.get("/channels/{channel_id}/stories", response_model=PaginatedAudioResponse)
async def list_stories(
        channel_id: str,
        page: int = Query(1, ge=1, le=1000, description="Page number for pagination"),
        page_size: int = Query(10, ge=1, le=100, description="Number of stories per page"),
        current_user: dict = Depends(JWTAuthGuard("user"))
):
    try :
        cache_key = process_cache_key()
        # Check cache
        cached_stories = await cache.h_get(cache_key, "channel_story", {"channel_id": channel_id, "page": page, "page_size": page_size})

        if cached_stories is not None:
            return cached_stories

        channel = await channel_service.find_channel_by_id(channel_id)
        if not channel:
            raise HTTPException(status_code=404, detail="Channel not found")
        if not channel.get("is_active", True):
            raise HTTPException(status_code=404, detail="Channel is not active")

        channel_info = {
            "youtube_channel_id": channel.get("youtube_channel_id", ""),
            "title": channel.get("title", "No title available"),
            "description": channel.get("description", "No description available"),
            "thumbnail_url": channel.get("thumbnail_url", "https://example.com/default_thumbnail.png")
        }

        stories = await audio_stories_service.get_audio_story_by_channel_id(channel_id=channel_id, page=page, page_size=page_size)

        if not stories:
            raise HTTPException(status_code=404, detail="No stories found for this channel")

        stories["channel"] = channel_info

        # Paginated response
        await cache.h_set(cache_key, "channel_story", stories, {"channel_id": channel_id, "page": page, "page_size": page_size})
        return stories
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Get audio file path for a specific story
@userRouter.get("/stories-audio/{story_id}")
async def fetch_audio(story_id: str, current_user: dict = Depends(JWTAuthGuard("user"))):
    if not story_id:
        raise HTTPException(status_code=400, detail="Story ID is required")
    if not story_id.isalnum():
        raise HTTPException(status_code=400, detail="Invalid Story ID format")

    # Fetch the audio story by ID
    story = await audio_stories_service.get_audio_story_by_id(story_id)
    if not story:
        raise HTTPException(status_code=404, detail="Audio story not found")

    signed_url = generate_signed_url(story["file_name"], expiry_seconds=86400)

    return {"signed_url": signed_url, "expires_in": 86400}

# Download audio file by filename
@userRouter.get("/audio-download/{filename}")
async def audio_download(filename: str, token: str = Query(...)):
    if not token:
        raise HTTPException(status_code=400, detail="Token is required")

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

# Update playlist
@userRouter.post("/channel/update-favourite", response_model=UserResponse)
async def update_favorite_channel(
        data: FavoriteChannel,
        current_user: dict = Depends(JWTAuthGuard("user"))
):
    try:
        user = await user_service.get_user_details_by_id(current_user.get("id"))
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        channel = await channel_service.find_channel_by_id(data.channel_id)
        if not channel or not channel.get("is_active", True):
            raise HTTPException(status_code=404, detail="Channel not found")

        set_favorite = True if ObjectId(data.channel_id) not in user.get("favorite_channels") else False

        # Update the favorite channel logic here
        updated_channel = await user_service.update_favourite_status(current_user.get("id"), data.channel_id, set_favorite)

        if not updated_channel:
            raise HTTPException(status_code=500, detail="Failed to update favorite channel")

        return updated_channel
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Create a new playlist
@userRouter.post("/manage/playlists", response_model=PlaylistCreateResponse)
async def create_playlist(data: PlaylistCreate, current_user: dict = Depends(JWTAuthGuard("user"))):
    try:
        user = await user_service.get_user_details_by_id(current_user.get("id"))
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if not len(data.videos):
            raise HTTPException(status_code=400, detail="Playlist must contain at least one video")

        try:
            videos = [ObjectId(v) for v in data.videos]
        except bson_errors.InvalidId:
            raise HTTPException(status_code=400, detail="Invalid video ID format")

        playlist_attributes = {
            "playlist_id": str(generate_unique_id()),
            "name": data.name,
            "videos": videos
        }

        # Create the playlist logic here
        result  = await user_service.create_playlist(current_user.get("id"), playlist_attributes)

        if not result :
            raise HTTPException(status_code=500, detail="Failed to create playlist")

        return {"status": True, "detail": "Playlist created successfully", "playlist_id": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))