# admins.py
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Union
from app.models import AdminCreate, AdminList
from app.services import AdminService
from auth.dependencies import JWTAuthGuard

apiRouter = APIRouter(
    prefix="/admins",
    tags=['admins']
)

@apiRouter.get("/list", response_model=List[AdminList])
def list_admins(current_user: str = Depends(JWTAuthGuard("admin"))):
    admin_service = AdminService()
    admins = admin_service.list_admins()

    if not admins:
        raise HTTPException(status_code=404, detail="No admins found.")

    return admins