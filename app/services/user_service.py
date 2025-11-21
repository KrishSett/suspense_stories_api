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

    # Find a user by ID
    async def find_user_by_id(self, user_id: str) -> Optional[dict]:
        try:
            user = await self.db.users.find_one(
                {"_id": ObjectId(user_id)},
                {"_id": 0, "firstname": 1, "lastname": 1, "email": 1, "is_active": 1},
            )
            if not user:
                self.logger.warning("User not found for ID %s", user_id)
                raise HTTPException(status_code=404, detail="User not found")

            self.logger.info("Fetched user profile for ID %s", user_id)
            return user
        except PyMongoError as e:
            self.logger.error("Error in %s for ID %s: %s", "find_user_by_id", user_id, e)
            raise HTTPException(status_code=500, detail="Could not fetch user data")
        except bson_errors.InvalidId:
            self.logger.warning("Invalid user ID provided: %s", user_id)
            raise HTTPException(status_code=400, detail="Invalid user ID")
        except Exception as e:
            self.logger.error("Error in %s for ID %s: %s", "find_user_by_id", user_id, e)
            raise HTTPException(
                status_code=500,
                detail="An unexpected error occurred while fetching user data",
            )

    # List of active users with pagination
    async def list_users(self, page: int = 1, page_size: int = 10) -> dict:
        try:
            skip = (page - 1) * page_size

            query = {"is_active": True}
            projection = {
                "_id": 0,
                "firstname": 1,
                "lastname": 1,
                "email": 1,
                "is_active": 1,
            }

            # Count total matching users
            total_users = await self.db.users.count_documents(query)

            # Fetch paginated users
            cursor = (
                self.db.users.find(query, projection)
                .sort("created_at", -1)  # Sort by created_at DESC
                .skip(skip)
                .limit(page_size)
            )

            result = await cursor.to_list(length=page_size)

            self.logger.info(
                "Fetched %d active users (page %d, page_size %d)",
                len(result), page, page_size
            )

            return {
                "total": total_users,
                "page": page,
                "page_size": page_size,
                "total_pages": (total_users + page_size - 1) // page_size,
                "data": result
            }

        except PyMongoError as e:
            self.logger.error("Error in list_users: %s", e)
            raise HTTPException(status_code=500, detail="Could not fetch users data")
        except Exception as e:
            self.logger.error("Error in list_users: %s", e)
            raise HTTPException(
                status_code=500,
                detail="An unexpected error occurred while fetching users data",
            )

    # Find user by email
    async def find_user_with_email(self, email: EmailStr) -> Optional[dict]:
        try:
            user = await self.db.users.find_one(
                {"email": email, "is_active": True},
                {"_id": 1, "firstname": 1, "lastname": 1, "email": 1, "password_hash": 1, "is_verified": 1},
            )
            if not user:
                self.logger.warning("User not found for email %s", email)
                return None

            self.logger.info("Found user with email: %s", email)
            return {
                "objectId": str(user["_id"]),
                "email": user["email"],
                "password_hash": str(user["password_hash"]),
                "is_verified": user["is_verified"]
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
    async def get_user_details_by_id(self, user_id: str) -> Optional[dict]:
        try:
            user = await self.db.users.find_one(
                {"_id": ObjectId(user_id), "is_active": True},
                {"_id": 0, "firstname": 1, "lastname": 1, "email": 1, "phone": 1, "favorite_channels": 1, "playlist": 1},
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
            raise HTTPException(status_code=500, detail=f"Could not update user data {e}")
        except bson_errors.InvalidId:
            self.logger.warning("Invalid user ID for update: %s", user_id)
            raise HTTPException(status_code=400, detail="Invalid user ID")
        except Exception as e:
            self.logger.error("Error in %s for ID %s: %s", "update_user", user_id, e)
            raise HTTPException(
                status_code=500,
                detail="An unexpected error occurred while updating user data",
            )

    # Find user by verification token
    async def find_by_verification_token(self, token: str) -> Optional[dict]:
        try:
            user = await self.db.users.find_one(
                {"verification_token": token, "is_active": True},
                {"_id": 1, "email": 1, "is_verified": 1},
            )
            if not user:
                self.logger.warning("User not found for verification token: %s", token)
                return None

            self.logger.info("Found user for verification token: %s", token)
            return {
                "_id": str(user["_id"])
            }
        except PyMongoError as e:
            self.logger.error(
                "Error in %s for token %s: %s", "find_by_verification_token", token, e
            )
            raise HTTPException(status_code=500, detail="Could not fetch user data")
        except Exception as e:
            self.logger.error(
                "Error in %s for token %s: %s", "find_by_verification_token", token, e
            )
            raise HTTPException(
                status_code=500,
                detail="An unexpected error occurred while fetching user data",
            )

    # Update favourite status of a channel
    async def update_favourite_status(self, user_id: str, channel_id: str, is_favourite: bool) -> Optional[dict]:
        try:

            if is_favourite:
                result = await self.db.users.update_one(
                    {"_id": ObjectId(user_id)},
                    {
                        "$push": {"favorite_channels": ObjectId(channel_id)},
                        "$set": {"updated_at": get_current_iso_timestamp()}
                    }
                )
            else:
                result = await self.db.users.update_one(
                    {"_id": ObjectId(user_id)},
                    {
                        "$pull": {"favorite_channels": ObjectId(channel_id)},
                        "$set": {"updated_at": get_current_iso_timestamp()}
                    }
                )

            if result.modified_count == 0:
                self.logger.warning("No changes made for channel ID %s", channel_id)
                raise HTTPException(status_code=404, detail="Channel not found or no changes made")

            self.logger.info("Favourite status updated for channel ID %s", channel_id)
            return {"status": True, "detail": "Favourite status updated successfully"}
        except bson_errors.InvalidId:
            self.logger.warning("Invalid channel ID for favourite update: %s", channel_id)
            raise HTTPException(status_code=400, detail="Invalid channel ID")
        except PyMongoError as e:
            self.logger.error("Error in %s for ID %s: %s", "update_favourite_status", channel_id, e)
            raise HTTPException(status_code=500, detail="Could not update favourite status")

    # Create a new playlist for a user
    async def create_playlist(self, user_id: str, playlist_data: dict) -> str:
        try:
            try:
                user_obj_id = ObjectId(user_id)
            except Exception:
                raise HTTPException(status_code=400, detail="Invalid user ID")

            result = await self.db.users.update_one(
                {"_id": user_obj_id},
                {
                    "$push": {"playlists": playlist_data},
                    "$set": {"updated_at": get_current_iso_timestamp()}
                }
            )

            if result.modified_count == 0:
                self.logger.warning("Playlist not created for user %s", user_id)
                raise HTTPException(status_code=404, detail="User not found")

            self.logger.info("Playlist '%s' created for user %s", playlist_data.get("name", "Playlist"), user_id)
            return playlist_data.get("playlist_id")
        except PyMongoError as e:
            self.logger.error("Error creating playlist for user %s: %s", user_id, e)
            raise HTTPException(status_code=500, detail="Could not create playlist")