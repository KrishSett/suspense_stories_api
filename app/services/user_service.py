# admin_services.py
from pydantic.v1 import EmailStr
from pymongo.errors import PyMongoError
from fastapi import HTTPException
from bson import ObjectId, errors as bson_errors
from app.services.base_service import BaseService
from typing import Optional

class UserService(BaseService):
    def __init__(self):
        super().__init__()

    # List of active users
    async def list_users(self) -> list:
        try:
            users = self.db.users.find(
                {"is_active": True},
                {"_id": 0, "firstname": 1, "lastname": 1, "email": 1}
            )
            return await users.to_list(length=None)
        except PyMongoError as e:
            raise HTTPException(status_code=500, detail="Could not fetch users data")
        except Exception as e:
            raise HTTPException(status_code=500, detail="An unexpected error occurred while fetching users data")

    # Find user by email and return objectId + email
    async def find_user_with_email(self, email: EmailStr) -> Optional[dict]:
        try:
            user = await self.db.users.find_one(
                {"email": email, "is_active": True},
                {"_id": 1, "firstname": 1, "lastname": 1, "email": 1, "password_hash": 1}
            )
            if not user:
                raise Exception("User not found")
            return {
                "objectId": str(user["_id"]),
                "email": user["email"],
                "password_hash": str(user["password_hash"])
            }
        except PyMongoError as e:
            raise HTTPException(status_code=500, detail="Could not fetch user data")
        except Exception as e:
            raise HTTPException(status_code=500, detail="An unexpected error occurred while fetching user data")

    # Get user profile by ID
    async def get_user_by_id(self, user_id: str) -> Optional[dict]:
        try:
            user = await self.db.users.find_one(
                {"_id": ObjectId(user_id), "is_active": True},
                {"_id": 0, "firstname": 1, "lastname": 1, "email": 1}
            )
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            return user
        except PyMongoError as e:
            raise HTTPException(status_code=500, detail="Could not fetch user data")
        except bson_errors.InvalidId:
            raise HTTPException(status_code=400, detail="Invalid user ID")
        except Exception as e:
            raise HTTPException(status_code=500, detail="An unexpected error occurred while fetching user data")