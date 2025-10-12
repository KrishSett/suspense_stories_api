# admin_services.py
from pydantic.v1 import EmailStr
from pymongo.errors import PyMongoError
from fastapi import HTTPException
from bson import ObjectId, errors as bson_errors
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
            self.logger.error("Error in %s: %s", "list_admins", e)
            raise HTTPException(status_code=500, detail="Could not fetch admin data")
        except Exception as e:
            self.logger.error("Unexpected error in %s: %s", "list_admins", e)
            raise HTTPException(status_code=500, detail="An unexpected error occurred while fetching admin data")

    # Find admin by email and return objectId + email
    async def find_admin_with_email(self, email: EmailStr) -> Optional[dict]:
        try:
            admin = await self.db.admins.find_one(
                {"email": email, "is_active": True},
                {"_id": 1, "firstname": 1, "lastname": 1, "email": 1, "password_hash": 1}
            )

            if not admin:
                self.logger.warning("Admin not found with email: %s", email)
                raise HTTPException(status_code=404, detail="Admin not found")

            return {
                "objectId": str(admin["_id"]),
                "email": admin["email"],
                "password_hash": str(admin["password_hash"]),
            }

        except PyMongoError as e:
            self.logger.error("Error in %s for email %s: %s", "find_admin_with_email", email, e)
            raise HTTPException(status_code=500, detail="Could not fetch admin data")
        except Exception as e:
            self.logger.error("Unexpected error in %s for email %s: %s", "find_admin_with_email", email, e)
            raise HTTPException(status_code=500, detail="An unexpected error occurred while fetching admin data")

    # Get admin profile by ID
    async def get_admin_by_id(self, admin_id: str) -> Optional[dict]:
        try:
            admin = await self.db.admins.find_one(
                {"_id": ObjectId(admin_id), "is_active": True},
                {"_id": 0, "firstname": 1, "lastname": 1, "email": 1}
            )

            if not admin:
                self.logger.warning("Admin not found with ID: %s", admin_id)
                raise HTTPException(status_code=404, detail="Admin not found")

            return admin

        except bson_errors.InvalidId:
            self.logger.warning("Invalid admin ID provided: %s", admin_id)
            raise HTTPException(status_code=400, detail="Invalid admin ID")
        except PyMongoError as e:
            self.logger.error("Error in %s for ID %s: %s", "get_admin_by_id", admin_id, e)
            raise HTTPException(status_code=500, detail="Could not fetch admin data")
        except Exception as e:
            self.logger.error("Unexpected error in %s for ID %s: %s", "get_admin_by_id", admin_id, e)
            raise HTTPException(status_code=500, detail="An unexpected error occurred while fetching admin data")
