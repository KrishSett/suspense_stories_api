# users.py
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import FileResponse
from auth.dependencies import JWTAuthGuard
from app.models import PlaylistCreate, PlaylistContentUpdate, PlaylistCreateResponse, PaginatedAudioResponse, PaginatedChannelsResponse, FavoriteChannel, UserResponse, UserProfileResponse, UserProfileUpdate, SignOutResponse, PlaylistContentsResponse
from app.services import AdminService, UserService, ChannelService, AudioStoriesService, PlaylistService
from common import RedisHashCache
from config import config
from utils.helpers import generate_signed_url, decode_signed_url_token, process_cache_key, generate_unique_id, generate_placeholder_img
from jose import JWTError
from bson import ObjectId, errors as bson_errors
import os

userRouter = APIRouter(prefix="/users", tags=["users"])
admin_service = AdminService()
user_service = UserService()
channel_service = ChannelService()
audio_stories_service = AudioStoriesService()
playlist_service = PlaylistService()
cache = RedisHashCache(prefix=config["cache_prefix"])

# User sign-out functionality
@userRouter.post("/sign-out", response_model=SignOutResponse)
async def user_logout(current_user: dict = Depends(JWTAuthGuard("user"))):
    try:
        user = await user_service.get_user_details_by_id(current_user.get("id"))
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        return {
            "status": True,
            "detail": "User sign out success"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Get User Profile
@userRouter.get("/profile", response_model=UserProfileResponse)
async def get_user_profile(current_user: dict = Depends(JWTAuthGuard("user"))):
    try:
        cache_key = process_cache_key()

        # Check cache
        cached_profile = await cache.h_get(cache_key, "user_profile", {"user_id": current_user.get("id")})
        if cached_profile is not None:
            return cached_profile

        # Fetch active user details
        user = await user_service.get_user_details_by_id(current_user.get("id"))
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        user_profile = {
            "firstname": user.get("firstname", ""),
            "lastname": user.get("lastname", ""),
            "email": user.get("email", ""),
            "phone": user.get("phone", ""),
            "profile_img": generate_placeholder_img(f"{user.get("firstname", "")[0]}{user.get("lastname", "")[0]}"),
            "is_active": True,
            "type": user.get("role", "user")
        }

        # Set user profile in cache
        await cache.h_set(cache_key, "user_profile", user_profile, {"user_id": current_user.get("id")})
        return user_profile
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Update User Profile
@userRouter.put("/profile", response_model=UserResponse)
async def update_user_profile(
        data: UserProfileUpdate,
        current_user: dict = Depends(JWTAuthGuard("user"))
):
    try:
        user = await user_service.get_user_details_by_id(current_user.get("id"))
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        update_data = {
            "firstname": data.firstname,
            "lastname": data.lastname,
            "phone": data.phone
        }

        updated_user = await user_service.update_user(current_user.get("id"), update_data)
        if not updated_user:
            raise HTTPException(status_code=500, detail="Failed to update user profile")

        # Invalidate cache
        cache_key = process_cache_key()
        await cache.h_del(cache_key, "user_profile", {"user_id": current_user.get("id")})

        return {
            "status": True,
            "detail": "User profile updated successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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

        stories["channel_info"] = channel_info

        # Paginated response
        await cache.h_set(cache_key, "channel_story", stories, {"channel_id": str(channel_id), "page": page, "page_size": page_size})
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

# Update favourite channel bookmark
@userRouter.post("/channel/update-favourite", response_model=UserResponse)
async def update_favorite_channel(
        data: FavoriteChannel,
        current_user: dict = Depends(JWTAuthGuard("user"))
):
    try:
        user = await user_service.get_user_details_by_id(current_user.get("id"))
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Check and validate the given channel Id
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
            videos = []
        else:
            try:
                videos = [ObjectId(v) for v in data.videos]
            except bson_errors.InvalidId:
                raise HTTPException(status_code=400, detail="Invalid video ID format")

        playlist_name = "My Playlist" if data.name.lower() != "my playlist" else data.name.title()

        playlist_attributes = {
            "playlist_id": str(generate_unique_id()),
            "name": playlist_name, #Name is hard coded to my playlist otherwise data.name
            "videos": videos
        }

        # Create the playlist for user
        result  = await playlist_service.create_playlist(current_user.get("id"), playlist_attributes)

        if not result :
            raise HTTPException(status_code=500, detail="Failed to create playlist")

        return {"status": True, "detail": "Playlist created successfully", "playlist_id": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Add video to playlist
@userRouter.put("/manage/playlists/videos", response_model=UserResponse)
async def add_video_to_playlist(
    data: PlaylistContentUpdate,
    current_user: dict = Depends(JWTAuthGuard("user"))
):
    try:
        user = await user_service.get_user_details_by_id(current_user.get("id"))
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Add video to playlist
        result = await playlist_service.add_video_to_playlist(
            current_user.get("id"),
            data.video_id
        )

        return {
            "status": True,
            "detail": result["message"]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Remove video from playlist
@userRouter.delete("/manage/playlists/videos", response_model=UserResponse)
async def remove_video_from_playlist(
    data: PlaylistContentUpdate,
    current_user: dict = Depends(JWTAuthGuard("user"))
):
    try:
        user = await user_service.get_user_details_by_id(current_user.get("id"))
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Remove video from playlist
        result = await playlist_service.remove_video_from_playlist(
            current_user.get("id"),
            data.video_id
        )

        return {
            "status": True,
            "detail": result["message"]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Remove an existing playlist of
@userRouter.delete("/manage/playlists", response_model=UserResponse)
async def delete_playlist(current_user: dict = Depends(JWTAuthGuard("user"))):
    try:
        user = await user_service.get_user_details_by_id(current_user.get("id"))
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Remove the playlist for user
        result  = await playlist_service.remove_playlist(current_user.get("id"))

        if not result :
            raise HTTPException(status_code=500, detail="Failed to remove playlist")

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Playlist contents retrieval
@userRouter.get("/playlist/contents", response_model=PlaylistContentsResponse)
async def get_playlist_contents(current_user: dict = Depends(JWTAuthGuard("user"))):
    try:
        user = await user_service.get_user_details_by_id(current_user.get("id"))

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Get the playlist contents for user
        playlist  = await playlist_service.get_user_playlist(current_user.get("id"))

        # Check if playlist exists
        if not playlist :
            raise HTTPException(status_code=500, detail="Failed to fetch playlist contents")

        user_playlist = await playlist_service.get_user_playlist_details(current_user.get("id"))

        # Check if playlist has videos
        if not user_playlist:
            raise HTTPException(status_code=404, detail="No contents found in the playlist")

        playlist_id = user_playlist.get("playlist_id", "")
        name = user_playlist.get("name", "")
        user_video_ids = list(map(str, user_playlist.get("videos", [])))

        playlist_videos = await audio_stories_service.get_audio_stories_by_ids(user_video_ids)

        if not playlist_videos:
            raise HTTPException(status_code=404, detail="No videos found in the playlist")

        return {
            "playlist_id": playlist_id,
            "name": name,
            "playlist_items": playlist_videos
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))