# audio_stories_service.py
from typing import Optional
from fastapi import HTTPException
from pymongo.errors import PyMongoError
from app.services.base_service import BaseService
from bson import ObjectId, errors as bson_errors
from utils.helpers import get_current_iso_timestamp

class AudioStoriesService(BaseService):
    def __init__(self):
        super().__init__()

    # Create a new audio story
    async def create_audio_story(self, story_data: dict, created_by: str) -> Optional[dict]:
        try:
            data_dict = story_data

            try:
                data_dict["created_by"] = ObjectId(created_by)
            except bson_errors.InvalidId:
                self.logger.warning("Invalid creator ID for audio story: %s", created_by)
                raise HTTPException(status_code=400, detail="Invalid creator ID")

            timestamp = get_current_iso_timestamp()
            data_dict["created_at"] = timestamp
            data_dict["updated_at"] = timestamp

            result = await self.db.audio_stories.insert_one(data_dict)

            self.logger.info(
                "Audio story created with ID %s for channel %s",
                str(result.inserted_id),
                story_data.get("channel_id"),
            )

            return {
                "story_id": str(result.inserted_id),
                "file_name": story_data["file_name"],
                "status": "queued",
            }

        except PyMongoError as e:
            self.logger.error(
                "Error in %s for channel %s: %s",
                "create_audio_story",
                story_data.get("channel_id"),
                e,
            )
            raise HTTPException(status_code=500, detail="Could not create audio story")
        except Exception as e:
            self.logger.error(
                "Unexpected error in %s for channel %s: %s",
                "create_audio_story",
                story_data.get("channel_id"),
                e,
            )
            raise HTTPException(
                status_code=500,
                detail="An unexpected error occurred while creating the audio story",
            )

    # Delete an audio story
    async def delete_audio_story(self, channel_id: str, story_id: str) -> bool:
        try:
            result = await self.db.audio_stories.delete_one(
                {
                    "_id": ObjectId(story_id),
                    "channel_id": ObjectId(channel_id),
                }
            )
            if result.deleted_count == 0:
                self.logger.warning("No audio story found to delete for ID %s", story_id)
                raise HTTPException(status_code=404, detail="Audio story not found")

            self.logger.info("Deleted audio story with ID %s", story_id)
            return True

        except bson_errors.InvalidId:
            self.logger.warning("Invalid audio story ID provided for delete: %s", story_id)
            raise HTTPException(status_code=400, detail="Invalid audio story ID")
        except PyMongoError as e:
            self.logger.error("Error in %s for story %s: %s", "delete_audio_story", story_id, e)
            raise HTTPException(status_code=500, detail="Could not delete audio story")
        except Exception as e:
            self.logger.error("Unexpected error in %s for story %s: %s", "delete_audio_story", story_id, e)
            raise HTTPException(
                status_code=500,
                detail="An unexpected error occurred while deleting the audio story",
            )

    # Mark an audio story as ready with metadata
    async def mark_ready(self, channel_id: str, file_path: str, meta_info: dict) -> bool:
        try:
            result = await self.db.audio_stories.update_one(
                {"channel_id": channel_id, "file_path": file_path},
                {
                    "$set": {
                        "is_ready": True,
                        "meta_details": meta_info,
                        "updated_at": get_current_iso_timestamp(),
                    }
                },
            )

            if result.modified_count == 0:
                self.logger.warning(
                    "No audio story updated as ready for channel %s with file %s",
                    channel_id,
                    file_path,
                )
            else:
                self.logger.info(
                    "Audio story marked ready for channel %s, file %s",
                    channel_id,
                    file_path,
                )

            return True

        except bson_errors.InvalidId:
            self.logger.warning("Invalid channel ID or file path: %s | %s", channel_id, file_path)
            raise HTTPException(status_code=400, detail="Invalid channel ID or file path")
        except PyMongoError as e:
            self.logger.error(
                "Error in %s for channel %s file %s: %s",
                "mark_ready",
                channel_id,
                file_path,
                e,
            )
            raise HTTPException(status_code=500, detail="Could not update audio story as ready")
        except Exception as e:
            self.logger.error(
                "Unexpected error in %s for channel %s file %s: %s",
                "mark_ready",
                channel_id,
                file_path,
                e,
            )
            raise HTTPException(status_code=500, detail="Could not update audio story as ready")

    # Get audio stories by channel ID with pagination
    async def get_audio_story_by_channel_id(self, channel_id: str, page: int = 1, page_size: int = 10) -> Optional[dict]:
        try:
            skip = (page - 1) * page_size

            query = {"channel_id": channel_id, "is_ready": True}
            projection = {"_id": 1, "meta_details": 1, "created_at": 1}

            # Count total matching stories
            total_stories = await self.db.audio_stories.count_documents(query)

            # Fetch paginated results sorted by created_at DESC
            cursor = (
                self.db.audio_stories
                .find(query, projection)
                .sort("created_at", -1)
                .skip(skip)
                .limit(page_size)
            )

            result = await cursor.to_list(length=page_size)

            if not result:
                self.logger.warning("No audio stories found for channel ID %s", channel_id)
                raise HTTPException(status_code=404, detail="Audio story not found")

            # Convert ObjectId to str and format response
            stories = [
                {
                    "story_id": str(story["_id"]),
                    "channel_id": str(story.get("channel_id", channel_id)),
                    "meta_details": story.get("meta_details", {})
                }
                for story in result
            ]

            self.logger.info(
                "Fetched %d stories for channel %s (page %d, page_size %d)",
                len(stories), channel_id, page, page_size
            )

            return {
                "total": total_stories,
                "page": page,
                "page_size": page_size,
                "total_pages": (total_stories + page_size - 1) // page_size,
                "data": stories
            }

        except Exception as e:
            self.logger.error(
                "Error in get_audio_story_by_channel_id for channel %s: %s",
                channel_id, e
            )
            raise HTTPException(status_code=500, detail="Could not fetch audio story data")

    # Get audio story file by ID
    async def get_audio_story_by_id(self, story_id: str) -> Optional[dict]:
        try:
            return await self.db.audio_stories.find_one(
                {"_id": ObjectId(story_id), "is_ready": True},
                {"_id": 0, "file_name": 1}
            )

        except bson_errors.InvalidId:
            self.logger.warning("Invalid audio story ID: %s", story_id)
            raise HTTPException(status_code=400, detail="Invalid audio story ID")

        except (PyMongoError, Exception) as e:
            self.logger.error(
                "Error in get_audio_story_by_id for ID %s: %s", story_id, e, exc_info=True
            )
            raise HTTPException(status_code=500, detail="Could not fetch audio story data")