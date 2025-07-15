# admins.py
from fastapi import APIRouter, HTTPException
from typing import List, Union
from app.models import AdminCreate, AdminList
from app.services import admin_services

apiRouter = APIRouter(
    prefix="/admins",
    tags=['admins']
)

@apiRouter.get("/list", response_model=List[AdminList])
def list_admins():
    admins = admin_services.list_admin()

    if not admins:
        raise HTTPException(status_code=404, detail="No admins found.")

    return admins