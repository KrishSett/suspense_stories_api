# admins.py
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query
from typing import List
import uuid
from auth.dependencies import JWTAuthGuard
from app.models import AdminList, PaginatedUserResponse, ChannelList, ChannelCreate, ChannelUpdate, ChannelResponse, ChannelSetOrder, PaginatedChannelsResponse, ChannelView, AudioStoryCreate, AudioStoryQueuedResponse
from app.services import AdminService, UserService, ChannelService, AudioStoriesService
from app.jobs import download_audio_and_get_info
from common import RedisHashCache
from config import config
from utils.helpers import process_cache_key
from fastapi.encoders import jsonable_encoder

adminRouter = APIRouter(
    prefix="/admins",
    tags=['admins']
)

# Instantiate once to avoid multiple unnecessary DB client initializations
admin_service = AdminService()
user_service = UserService()
channel_service = ChannelService()
audio_stories_service = AudioStoriesService()
cache = RedisHashCache(prefix=config["cache_prefix"])

# List all active admins
@adminRouter.get("/list", response_model=List[AdminList])
async def list_admins(current_user: dict = Depends(JWTAuthGuard("admin"))):
    try:
        cache_key = process_cache_key()
        admins = await cache.h_get(cache_key, "list_admins")

        if admins is not None:
            return admins

        admins = await admin_service.list_admins()

        if not admins:
            raise HTTPException(status_code=404, detail="No admins found.")

        # Cache the list of admins
        await cache.h_set(cache_key, "list_admins", admins)
        return admins
    except HTTPException:
        raise  # Re-raise so FastAPI handles it properly
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Get admin profile by ID
@adminRouter.get("/profile", response_model=AdminList)
async def admin_profile(current_user: dict = Depends(JWTAuthGuard("admin"))):
    try:
        admin = await admin_service.get_admin_by_id(str(current_user["id"]))
        if not admin:
            raise HTTPException(status_code=404, detail="Admin not found.")
        return admin
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Create a new channel
@adminRouter.post("/channel-create", response_model=ChannelList)
async def create_channel(
    data: ChannelCreate,
    current_user: dict = Depends(JWTAuthGuard("admin"))
):
    try:
        channel_data = {
            "youtube_channel_id": data.youtube_channel_id,
            "title": data.title,
            "is_active": data.is_active,
            "order_position": data.order_position,
            "description" : data.description,
            "thumbnail_url": data.thumbnail_url,
            "created_at": None,
            "updated_at": None,
            "published_at": None,
            "created_by": None
        }

        # Inject current user's ID into created_by
        created_by = str(current_user["id"])
        created_channel = await channel_service.create_channel(channel_data, created_by)

        # Delete cache for active channels
        cache_key = process_cache_key()
        await cache.h_del_wildcard(cache_key, "list_active_channels")
        return created_channel
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Update channel status (activate/deactivate)
@adminRouter.post("/channel/update-status/{channel_id}", response_model=ChannelResponse)
async def update_channel_status(
    channel_id: str,
    current_user: dict = Depends(JWTAuthGuard("admin"))
):
    try:
        # Find channel first
        channel = await channel_service.find_channel_by_id(channel_id)
        if not channel:
            raise HTTPException(status_code=404, detail="Channel not found.")

        # Toggle the status
        new_status = not channel.get("is_active", False)

        updated = await channel_service.update_channel(channel_id, {"is_active": new_status})
        if not updated:
            raise HTTPException(status_code=500, detail="Failed to update channel status.")

        # Delete cache for active channels
        cache_key = process_cache_key()
        await cache.h_del_wildcard(cache_key, "list_active_channels")

        return {
            "status": True,
            "detail": f"Channel {'activated' if new_status else 'deactivated'} successfully."
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Set the order of a channel
@adminRouter.post("/channel-set-order", response_model=ChannelResponse)
async def set_channel_order(data: ChannelSetOrder, current_user: dict = Depends(JWTAuthGuard("admin"))):
    try:
        channel_id = data.channel_id
        order_position = data.order_position

        # Update channel order-position
        result = await channel_service.set_channel_order(channel_id, order_position)
        if not result:
            raise HTTPException(status_code=404, detail="Channel not found or order update failed.")

        # Delete cache for active channels
        cache_key = process_cache_key()
        await cache.h_del_wildcard(cache_key, "list_active_channels")
        return {"status": True, "detail": "Channel order updated successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# List all active channels
@adminRouter.get("/channel-list", response_model=PaginatedChannelsResponse)
async def list_active_channels(
        page: int = Query(1, ge=1, le=1000, description="Page number for pagination"),
        page_size: int = Query(10, ge=1, le=100, description="Number of channels per page"),
        current_user: dict = Depends(JWTAuthGuard("admin"))
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

        await cache.h_set(cache_key, "list_active_channels", jsonable_encoder(channels), {"page": page, "page_size": page_size})
        return channels
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Get a channel byID
@adminRouter.get('/channel/{channel_id}', response_model=ChannelView)
async def get_channel_by_id(channel_id: str, current_user: dict = Depends(JWTAuthGuard("admin"))):
    try:
        channel = await channel_service.find_channel_by_id(channel_id)
        if not channel:
            raise HTTPException(status_code=404, detail="Channel not found.")
        return {
                "channel_id": str(channel["_id"]),
                "youtube_channel_id": channel["youtube_channel_id"],
                "title": channel["title"],
                "is_active": channel.get("is_active", True),
                "order_position": channel["order_position"],
                "description": channel.get("description") or "No description available",
                "thumbnail_url": channel.get("thumbnail_url") or "https://example.com/default_thumbnail.png",
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Update a channel
@adminRouter.put("/channel-update", response_model=ChannelResponse)
async def update_channel(data: ChannelUpdate, current_user: dict = Depends(JWTAuthGuard("admin"))):
    try:
        channel_id = data.channel_id
        update_data = {
            "description": data.description,
            "thumbnail_url": data.thumbnail_url,
            "updated_at": None
        }

        updated_channel = await channel_service.update_channel(channel_id, update_data)
        if not updated_channel:
            raise HTTPException(status_code=404, detail="Channel not found.")

        # Delete cache for active channels
        cache_key = process_cache_key()
        await cache.h_del_wildcard(cache_key, "list_active_channels")
        return {"status": True, "detail": "Channel updated successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Create a new audio story
@adminRouter.post("/story-create", response_model=AudioStoryQueuedResponse)
async def create_audio_story(
    data: AudioStoryCreate,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(JWTAuthGuard("admin"))
):
    # Validate channel exists and is active
    channel = await channel_service.find_channel_by_id(data.channel_id)
    if not channel:
        raise HTTPException(status_code=400, detail="Channel is invalid or inactive.")

    file_name = f"story_{uuid.uuid4().hex}.m4a"
    story_data = {
        "channel_id": data.channel_id,
        "file_path": data.file_path,
        "file_name": file_name,
        "is_ready": False,
        "meta_details": None
    }
    created_by = str(current_user["id"])
    audio_story = await audio_stories_service.create_audio_story(story_data, created_by)
    background_tasks.add_task(
        download_audio_and_get_info,
        file_path=data.file_path,
        file_name=file_name,
        user_email=current_user["sub"],
        channel_id=data.channel_id
    )

    # Delete cache for the specific channel's stories
    cache_key = process_cache_key()
    await cache.h_del_wildcard(cache_key, f"channel_story|channel_id={data.channel_id}")
    return audio_story

# Remove an audio story
@adminRouter.delete("/story/{channel_id}/{story_id}/delete", response_model=ChannelResponse)
async def delete_audio_story(channel_id: str, story_id: str, current_user: dict = Depends(JWTAuthGuard("admin"))):
    try:
        deleted = await audio_stories_service.delete_audio_story(channel_id=channel_id, story_id=story_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Audio story not found.")

        # Delete cache for the specific channel's stories
        cache_key = process_cache_key()
        await cache.h_del_wildcard(cache_key, f"channel_story|channel_id={channel_id}")
        return {"detail": "Audio story deleted successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Update user status (activate/deactivate)
@adminRouter.post("/user/update-status/{user_id}", response_model=ChannelResponse)
async def update_user_status(
    user_id: str,
    current_user: dict = Depends(JWTAuthGuard("admin"))
):
    try:
        # Find user first
        user = await user_service.find_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found.")

        # Toggle the status
        new_status = not user.get("is_active", False)

        updated = await user_service.update_user(
            user_id=user_id,
            update_data={"is_active": new_status}
        )
        if not updated:
            raise HTTPException(status_code=500, detail="Failed to update user status.")

        # Delete cache for user list
        cache_key = process_cache_key()
        await cache.h_del(cache_key, "list_users")
        return {"detail": f"User {'activated' if new_status else 'deactivated'} successfully."}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Users list
@adminRouter.get("/user/list", response_model=PaginatedUserResponse)
async def list_users(
        page:int =  Query(1, ge=1, le=1000, description="Page number for pagination"),
        page_size:int = Query(10, ge=1, le=100, description="Number of users per page"),
        current_user: dict = Depends(JWTAuthGuard("admin"))
):
    try:
        cache_key = process_cache_key()

        # Check cache
        cached_users = await cache.h_get(cache_key, "list_users")
        if cached_users is not None:
            return cached_users

        users = await user_service.list_users()
        if not users:
            raise HTTPException(status_code=404, detail="No users found.")

        # Cache the list of users
        await cache.h_set(cache_key, "list_users", jsonable_encoder(users), {"page": page, "page_size": page_size})
        return users
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))