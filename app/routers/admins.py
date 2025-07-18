from fastapi import APIRouter, HTTPException, Depends
from typing import List
from app.models import AdminList
from app.services import AdminService
from auth.dependencies import JWTAuthGuard

apiRouter = APIRouter(
    prefix="/admins",
    tags=['admins']
)

# Instantiate once to avoid multiple unnecessary DB client initializations
admin_service = AdminService()

@apiRouter.get("/list", response_model=List[AdminList])
async def list_admins(current_user: str = Depends(JWTAuthGuard("admin"))):
    try:
        admins = await admin_service.list_admins()

        if not admins:
            raise HTTPException(status_code=404, detail="No admins found.")

        return admins
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error retrieving admin list.")
