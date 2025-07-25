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

apiRouter = APIRouter(
    prefix="/admins",
    tags=['admins']
)

# Instantiate once to avoid multiple unnecessary DB client initializations
admin_service = AdminService()
channel_service = ChannelService()
audio_stories_service = AudioStoriesService()

@apiRouter.get("/list", response_model=List[AdminList])
async def list_admins(current_user: dict = Depends(JWTAuthGuard("admin"))):
    cache = RedisHashCache(cache_key="admin_list")

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


@apiRouter.post("/channel-create", response_model=ChannelList)
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

@apiRouter.post("/story-create", response_model=AudioStoryQueuedResponse)
async def create_audio_story(data: AudioStoryCreate, background_tasks: BackgroundTasks, current_user: dict = Depends(JWTAuthGuard("admin"))):
    # Generate unique file name
    file_name = f"story_{uuid.uuid4().hex}.m4a"

    story_data = {
        "channel_id": data.channel_id,
        "file_path": data.file_path,
        "file_name": file_name,
        "is_ready": False,
        "meta_details": None
    }

    # Insert into MongoDB
    created_by = str(current_user["id"])
    audio_story =  await audio_stories_service.create_audio_story(story_data, created_by)

    # Enqueue background job with email
    background_tasks.add_task(download_audio_and_get_info, file_path=data.file_path, file_name=file_name, user_email=current_user["sub"], channel_id=data.channel_id)

    return audio_story
