# playlist_services.py
from pydantic.v1 import EmailStr
from pymongo.errors import PyMongoError
from fastapi import HTTPException
from bson import ObjectId, errors as bson_errors
from app.services.base_service import BaseService
from typing import Optional
from utils.helpers import get_current_iso_timestamp

class PlaylistService(BaseService):
    def __init__(self):
        super().__init__()

    # Create a new playlist for a user
    async def create_playlist(self, user_id: str, playlist_data: dict) -> str:
        try:
            try:
                user_obj_id = ObjectId(user_id)
            except Exception:
                raise HTTPException(status_code=400, detail="Invalid user ID")

            # Check if playlist already exists for the user
            playlist_exists = await self.get_user_playlist(user_id)
            if playlist_exists:
                self.logger.error("Playlist already exists for user %s", user_id)
                raise HTTPException(status_code=409, detail="Playlist already exists for user")

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

    # Get a user's playlist ID
    async def get_user_playlist(self, user_id: str) -> Optional[str]:
        try:
            user_obj_id = ObjectId(user_id)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid user ID")

        try:
            user = await self.db.users.find_one(
                {"_id": user_obj_id},
                {"playlists.playlist_id": 1, "_id": 0}
            )

            # Safe checks against missing keys or empty array
            playlists = user.get("playlists") if user else None

            if not playlists or not isinstance(playlists, list):
                raise HTTPException(status_code=404, detail="Playlist not set for user")

            playlist = playlists[0] if playlists else None

            if not playlist or "playlist_id" not in playlist:
                raise HTTPException(status_code=500, detail="Corrupt playlist data")

            return playlist["playlist_id"]

        except PyMongoError as e:
            self.logger.error(f"DB error in get_user_playlist({user_id}): {e}")
            return None
        except HTTPException as e:
            return None

    # Check a playlist exists for a user with given ID
    async def check_playlist_valid(self, user_id: str, playlist_id: str) -> bool:
        try:
            try :
                user_obj_id = ObjectId(user_id)
            except bson_errors.InvalidId:
                self.logger.warning("Invalid user ID provided: %s", user_id)
                return False

            playlist = await self.db.users.find_one(
                {
                    "_id": user_obj_id,
                    "playlists": {
                        "$elemMatch": {"playlist_id": playlist_id}
                    }
                },
                {"playlists.$": 1}
            )

            if not playlist:
                self.logger.warning("Playlist ID %s not found for user %s", playlist_id, user_id)
                return False

            self.logger.info("Playlist ID %s found for user %s", playlist_id, user_id)
            return True
        except PyMongoError as e:
            self.logger.error("Error in %s for playlist ID %s: %s", "check_playlist_valid", playlist_id, e)
            return False

    # Add a single video to user's playlist
    async def add_video_to_playlist(self, user_id: str, video_id: str) -> dict:
        try:
            # Validate user ID
            try:
                user_obj_id = ObjectId(user_id)
            except Exception:
                raise HTTPException(status_code=400, detail="Invalid user ID")

            # Validate video ID
            try:
                video_obj_id = ObjectId(video_id)
            except Exception:
                raise HTTPException(status_code=400, detail="Invalid video ID")

            # Check if playlist exists
            playlist_id = await self.get_user_playlist(user_id)
            if not playlist_id:
                raise HTTPException(status_code=404, detail="Playlist not found")

            # Check if video already exists in playlist
            user = await self.db.users.find_one(
                {
                    "_id": user_obj_id,
                    "playlists.playlist_id": playlist_id,
                    "playlists.videos": video_obj_id
                }
            )

            if user:
                self.logger.info("Video %s already exists in playlist for user %s", video_id, user_id)
                return {
                    "status": True,
                    "message": "Video already in playlist",
                    "already_exists": True
                }

            # Add video to playlist
            result = await self.db.users.update_one(
                {
                    "_id": user_obj_id,
                    "playlists.playlist_id": playlist_id
                },
                {
                    "$push": {"playlists.$.videos": video_obj_id},
                    "$set": {"updated_at": get_current_iso_timestamp()}
                }
            )

            if result.modified_count == 0:
                raise HTTPException(status_code=404, detail="Failed to add video to playlist")

            self.logger.info("Video %s added to playlist for user %s", video_id, user_id)
            return {
                "status": True,
                "message": "Video added to playlist successfully",
                "already_exists": False
            }

        except PyMongoError as e:
            self.logger.error("Error adding video to playlist for user %s: %s", user_id, e)
            raise HTTPException(status_code=500, detail="Could not add video to playlist")

    # Remove a single video from user's playlist
    async def remove_video_from_playlist(self, user_id: str, video_id: str) -> dict:
        try:
            # Validate user ID
            try:
                user_obj_id = ObjectId(user_id)
            except Exception:
                raise HTTPException(status_code=400, detail="Invalid user ID")

            # Validate video ID
            try:
                video_obj_id = ObjectId(video_id)
            except Exception:
                raise HTTPException(status_code=400, detail="Invalid video ID")

            # Check if playlist exists
            playlist_id = await self.get_user_playlist(user_id)
            if not playlist_id:
                raise HTTPException(status_code=404, detail="Playlist not found")

            # Remove video from playlist (no error if video doesn't exist)
            result = await self.db.users.update_one(
                {
                    "_id": user_obj_id,
                    "playlists.playlist_id": playlist_id
                },
                {
                    "$pull": {"playlists.$.videos": video_obj_id},
                    "$set": {"updated_at": get_current_iso_timestamp()}
                }
            )

            if result.matched_count == 0:
                raise HTTPException(status_code=404, detail="Playlist not found")

            self.logger.info("Video %s removed from playlist for user %s", video_id, user_id)
            return {
                "status": True,
                "message": "Video removed from playlist successfully"
            }

        except PyMongoError as e:
            self.logger.error("Error removing video from playlist for user %s: %s", user_id, e)
            raise HTTPException(status_code=500, detail="Could not remove video from playlist")

    # Remove a user's playlist
    async def remove_playlist(self, user_id: str) -> dict:
        try:
            try:
                user_obj_id = ObjectId(user_id)
            except Exception:
                raise HTTPException(status_code=400, detail="Invalid user ID")

            playlist_id = await self.get_user_playlist(user_id)

            if playlist_id is None:
                raise HTTPException(status_code=404, detail="No playlist found to remove")

            result = await self.db.users.update_one(
                {"_id": user_obj_id},
                {"$unset": {"playlists": ""},
                 "$set": {"updated_at": get_current_iso_timestamp()}}
            )

            if result.modified_count == 0:
                raise HTTPException(status_code=404, detail="Playlist not removed")

            self.logger.info("Playlist removed for user %s", user_id)
            return {
                "status": True,
                "detail": "Playlist removed successfully"
            }

        except PyMongoError as e:
            self.logger.error("Error removing playlist for %s: %s", user_id, e)
            raise HTTPException(status_code=500, detail="Could not remove playlist")