# admin_services.py
from pydantic.v1 import EmailStr
from pymongo.errors import PyMongoError
from fastapi import HTTPException
from app.services.base_service import BaseService
from typing import Optional

class AdminService(BaseService):
    def __init__(self):
        super().__init__()

    # List of active admins
    async def list_admins(self) -> Optional[list]:
        try:
            admins = self.db.admins.find(
                {"is_active": True},
                {"_id": 0, "firstname": 1, "lastname": 1, "email": 1}
            )
            return await admins.to_list(length=None)
        except PyMongoError as e:
            raise HTTPException(status_code=500, detail="Could not fetch admin data")


    # Find admin by email and return objectId + email
    async def find_admin_with_email(self, email: EmailStr):
        try:
            admin = await self.db.admins.find_one(
                {"email": email, "is_active": True},
                {"_id": 1, "firstname": 1, "lastname": 1, "email": 1, "password_hash": 1}
            )
            return {
                "objectId": str(admin["_id"]),
                "email": admin["email"],
                "password_hash": str(admin["password_hash"])
            }
        except PyMongoError as e:
            print(f"Database error: {e}")
            raise HTTPException(status_code=500, detail="Could not fetch admin data")
