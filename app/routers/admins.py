# admins.py

from fastapi import APIRouter
from pydantic import BaseModel
import app.services.admin_services as admin

apiRouter = APIRouter(
    prefix="/admins",
    tags=['admins']
)

class Admin(BaseModel):
    firstname: str
    lastname: str
    email: str
    password: str

@apiRouter.get("/")
def list_admins():
    return admin.list_admin()
