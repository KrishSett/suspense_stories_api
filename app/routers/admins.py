# admins.py
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import List
import uuid
from auth.dependencies import JWTAuthGuard
from app.models import AdminList
from app.models import ChannelList, ChannelCreate
from app.models.audio_story_model import AudioStoryCreate, AudioStoryQueuedResponse
from app.services import AdminService, ChannelService, AudioStoriesService
from app.jobs import download_audio_and_get_info
from common import RedisHashCache
from config import config

adminRouter = APIRouter(
    prefix="/admins",
    tags=['admins']
)

# Instantiate once to avoid multiple unnecessary DB client initializations
admin_service = AdminService()
channel_service = ChannelService()
audio_stories_service = AudioStoriesService()
cache = RedisHashCache(prefix=config["cache_prefix"])

# List all active admins
@adminRouter.get("/list", response_model=List[AdminList])
async def list_admins(current_user: dict = Depends(JWTAuthGuard("admin"))):
    try:
        admins = await cache.h_get("list_admins")

        if admins is not None:
            return admins

        admins = await admin_service.list_admins()

        if not admins:
            raise HTTPException(status_code=404, detail="No admins found.")

        await cache.h_set(field="list_admins", value=admins, ttl=1500)
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
            "order_position": data.order_position
        }

        # Inject current user's ID into created_by
        created_by = str(current_user["id"])
        created_channel = await channel_service.create_channel(channel_data, created_by)
        return created_channel
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Deactivate a channel
@adminRouter.post("/channel-deactivate/{channel_id}")
async def deactivate_channel(channel_id: str, current_user: dict = Depends(JWTAuthGuard("admin"))):
    try:
        updated = await channel_service.update_channel(channel_id, {"is_active": False})
        if not updated:
            raise HTTPException(status_code=404, detail="Channel not found.")
        return {"detail": "Channel deactivated successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Activate a channel
@adminRouter.post("/channel-activate/{channel_id}")
async def activate_channel(channel_id: str, current_user: dict = Depends(JWTAuthGuard("admin"))):
    try:
        updated = await channel_service.update_channel(channel_id, {"is_active": True})
        if not updated:
            raise HTTPException(status_code=404, detail="Channel not found.")
        return {"detail": "Channel activated successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Set the order of a channel
@adminRouter.post("/channel-set-order/{channel_id}")
async def set_channel_order(channel_id: str, order_position: int, current_user: dict = Depends(JWTAuthGuard("admin"))):
    try:
        result = await channel_service.set_channel_order(channel_id, order_position)
        if not result:
            raise HTTPException(status_code=404, detail="Channel not found or order update failed.")
        return {"detail": "Channel order updated successfully."}
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
    if not channel or not channel.get("is_active", False):
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
@adminRouter.delete("/story-delete/{story_id}")
async def delete_audio_story(story_id: str, current_user: dict = Depends(JWTAuthGuard("admin"))):
    try:
        deleted = await audio_stories_service.delete_audio_story(story_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Audio story not found.")
        return {"detail": "Audio story deleted successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


