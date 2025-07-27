# user_services.py
from pydantic.v1 import EmailStr
from pymongo.errors import PyMongoError
from fastapi import HTTPException
from bson import ObjectId, errors as bson_errors
from app.services.base_service import BaseService
from typing import Optional
from utils.helpers import get_current_iso_timestamp


class UserService(BaseService):
    def __init__(self):
        super().__init__()

    # Create a new user
    async def create_user(self, user_data: dict) -> Optional[dict]:
        try:
            timestamp = get_current_iso_timestamp()
            user_data["created_at"] = timestamp
            user_data["updated_at"] = timestamp
            user = await self.db.users.insert_one(user_data)

            self.logger.info("User created successfully: %s", user_data.get("email"))
            return {
                "objectId": str(user.inserted_id),
                "email": user_data["email"],
                "status": True,
            }
        except PyMongoError as e:
            self.logger.error(
                "Error in %s for user %s: %s", "create_user", user_data.get("email"), e
            )
            raise HTTPException(status_code=500, detail="Could not create user")
        except Exception as e:
            self.logger.error(
                "Error in %s for user %s: %s", "create_user", user_data.get("email"), e
            )
            raise HTTPException(
                status_code=500,
                detail="An unexpected error occurred while creating the user",
            )

    # List of active users
    async def list_users(self) -> list:
        try:
            users = self.db.users.find(
                {"is_active": True},
                {"_id": 0, "firstname": 1, "lastname": 1, "email": 1},
            )
            result = await users.to_list(length=None)

            self.logger.info("Fetched %d active users", len(result))
            return result
        except PyMongoError as e:
            self.logger.error("Error in %s: %s", "list_users", e)
            raise HTTPException(status_code=500, detail="Could not fetch users data")
        except Exception as e:
            self.logger.error("Error in %s: %s", "list_users", e)
            raise HTTPException(
                status_code=500,
                detail="An unexpected error occurred while fetching users data",
            )

    # Find user by email
    async def find_user_with_email(self, email: EmailStr) -> Optional[dict]:
        try:
            user = await self.db.users.find_one(
                {"email": email, "is_active": True},
                {"_id": 1, "firstname": 1, "lastname": 1, "email": 1, "password_hash": 1},
            )
            if not user:
                self.logger.warning("User not found for email %s", email)
                return None

            self.logger.info("Found user with email: %s", email)
            return {
                "objectId": str(user["_id"]),
                "email": user["email"],
                "password_hash": str(user["password_hash"]),
            }
        except PyMongoError as e:
            self.logger.error(
                "Error in %s for email %s: %s", "find_user_with_email", email, e
            )
            raise HTTPException(status_code=500, detail="Could not fetch user data")
        except Exception as e:
            self.logger.error(
                "Error in %s for email %s: %s", "find_user_with_email", email, e
            )
            raise HTTPException(
                status_code=500,
                detail="An unexpected error occurred while fetching user data",
            )

    # Get user profile by ID
    async def get_user_by_id(self, user_id: str) -> Optional[dict]:
        try:
            user = await self.db.users.find_one(
                {"_id": ObjectId(user_id), "is_active": True},
                {"_id": 0, "firstname": 1, "lastname": 1, "email": 1},
            )
            if not user:
                self.logger.warning("User not found for ID %s", user_id)
                raise HTTPException(status_code=404, detail="User not found")

            self.logger.info("Fetched user profile for ID %s", user_id)
            return user
        except PyMongoError as e:
            self.logger.error("Error in %s for ID %s: %s", "get_user_by_id", user_id, e)
            raise HTTPException(status_code=500, detail="Could not fetch user data")
        except bson_errors.InvalidId:
            self.logger.warning("Invalid user ID provided: %s", user_id)
            raise HTTPException(status_code=400, detail="Invalid user ID")
        except Exception as e:
            self.logger.error("Error in %s for ID %s: %s", "get_user_by_id", user_id, e)
            raise HTTPException(
                status_code=500,
                detail="An unexpected error occurred while fetching user data",
            )

    # Update user details
    async def update_user(self, user_id: str, update_data: dict) -> Optional[dict]:
        try:
            update_data["updated_at"] = get_current_iso_timestamp()
            result = await self.db.users.update_one(
                {"_id": ObjectId(user_id)}, {"$set": update_data}
            )

            if result.modified_count == 0:
                self.logger.warning(
                    "No user updated (not found or no changes) for ID %s", user_id
                )
                raise HTTPException(
                    status_code=404,
                    detail="User not found or no changes made",
                )

            self.logger.info("User updated successfully: %s", user_id)
            return {"status": True, "message": "User updated successfully"}
        except PyMongoError as e:
            self.logger.error("Error in %s for ID %s: %s", "update_user", user_id, e)
            raise HTTPException(status_code=500, detail="Could not update user data")
        except bson_errors.InvalidId:
            self.logger.warning("Invalid user ID for update: %s", user_id)
            raise HTTPException(status_code=400, detail="Invalid user ID")
        except Exception as e:
            self.logger.error("Error in %s for ID %s: %s", "update_user", user_id, e)
            raise HTTPException(
                status_code=500,
                detail="An unexpected error occurred while updating user data",
            )
