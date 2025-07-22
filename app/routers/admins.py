# admins.py
from fastapi import APIRouter, HTTPException, Depends
from typing import List
from app.models import AdminList
from app.models import ChannelList, ChannelCreate
from app.services import AdminService, ChannelService
from auth.dependencies import JWTAuthGuard

apiRouter = APIRouter(
    prefix="/admins",
    tags=['admins']
)

# Instantiate once to avoid multiple unnecessary DB client initializations
admin_service = AdminService()
channel_service = ChannelService()

@apiRouter.get("/list", response_model=List[AdminList])
async def list_admins(current_user: dict = Depends(JWTAuthGuard("admin"))):
    try:
        admins = await admin_service.list_admins()

        if not admins:
            raise HTTPException(status_code=404, detail="No admins found.")

        return admins
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error retrieving admin list.")


@apiRouter.post("/channel-create")
async def create_channel(
    channel_data: ChannelCreate,
    current_user: dict = Depends(JWTAuthGuard("admin"))
):
    try:
        # Inject current user's ID into created_by
        created_by = str(current_user["id"])
        created_channel = await channel_service.create_channel(channel_data, created_by)

        return {
            "success": True,
            "channel_id": str(created_channel["_id"])
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
