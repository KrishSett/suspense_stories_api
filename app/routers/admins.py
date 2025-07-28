# admins.py
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import List
import uuid
from auth.dependencies import JWTAuthGuard
from app.models import AdminList
from app.models import ChannelList, ChannelCreate, ChannelUpdate, ChannelResponse, ChannelSetOrder, ChannelActiveList, ChannelView
from app.models.audio_story_model import AudioStoryCreate, AudioStoryQueuedResponse
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
        key = current_user["role"] + "_key"
        cache_key = process_cache_key(key)
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
        key = current_user["role"] + "_key"
        cache_key = process_cache_key(key)
        await cache.h_del(cache_key, "list_active_channels")
        return created_channel
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Deactivate a channel
@adminRouter.post("/channel-deactivate/{channel_id}", response_model=ChannelResponse)
async def deactivate_channel(channel_id: str, current_user: dict = Depends(JWTAuthGuard("admin"))):
    try:
        updated = await channel_service.update_channel(channel_id, {"is_active": False})
        if not updated:
            raise HTTPException(status_code=404, detail="Channel not found.")

        # Delete cache for active channels
        key = current_user["role"] + "_key"
        cache_key = process_cache_key(key)
        await cache.h_del(cache_key, "list_active_channels")
        return {"status": True, "detail": "Channel deactivated successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Activate a channel
@adminRouter.post("/channel-activate/{channel_id}", response_model=ChannelResponse)
async def activate_channel(channel_id: str, current_user: dict = Depends(JWTAuthGuard("admin"))):
    try:
        updated = await channel_service.update_channel(channel_id, {"is_active": True})
        if not updated:
            raise HTTPException(status_code=404, detail="Channel not found.")

        # Delete cache for active channels
        key = current_user["role"] + "_key"
        cache_key = process_cache_key(key)
        await cache.h_del(cache_key, "list_active_channels")
        return {"status": True, "detail": "Channel activated successfully."}
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
        key = current_user["role"] + "_key"
        cache_key = process_cache_key(key)
        await cache.h_del(cache_key, "list_active_channels")
        return {"status": True, "detail": "Channel order updated successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# List all active channels
@adminRouter.get("/channel-list", response_model=List[ChannelActiveList])
async def list_active_channels(current_user: dict = Depends(JWTAuthGuard("admin"))):
    try:
        key = f"{current_user['role']}_key"
        cache_key = process_cache_key(key)

        #Check cache
        cached_channels = await cache.h_get(cache_key, "list_active_channels")
        if cached_channels is not None:
            return cached_channels

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

        await cache.h_set(cache_key, "list_active_channels", jsonable_encoder(channels))
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
        key = current_user["role"] + "_key"
        cache_key = process_cache_key(key)
        await cache.h_del(cache_key, "list_active_channels")
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
    return audio_story

# Remove an audio story
@adminRouter.delete("/story-delete/{story_id}", response_model=ChannelResponse)
async def delete_audio_story(story_id: str, current_user: dict = Depends(JWTAuthGuard("admin"))):
    try:
        deleted = await audio_stories_service.delete_audio_story(story_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Audio story not found.")
        return {"detail": "Audio story deleted successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Deactivate a user
@adminRouter.post("/user-deactivate/{user_id}")
async def deactivate_user(user_id: str, current_user: dict = Depends(JWTAuthGuard("admin"))):
    try:
        updated = await user_service.update_user(user_id=user_id, update_data={"is_active": False})
        if not updated:
            raise HTTPException(status_code=404, detail="User not found.")
        return {"detail": "User deactivated successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Activate a user
@adminRouter.post("/user-activate/{user_id}")
async def deactivate_user(user_id: str, current_user: dict = Depends(JWTAuthGuard("admin"))):
    try:
        updated = await user_service.update_user(user_id=user_id, update_data={"is_active": True})
        if not updated:
            raise HTTPException(status_code=404, detail="User not found.")
        return {"detail": "User activated successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))