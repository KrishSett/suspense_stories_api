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

    # Create a new channel
    async def create_audio_story(self, story_data: dict, created_by: str) -> Optional[dict]:
        try:
            data_dict = story_data

            try:
                data_dict["created_by"] = ObjectId(created_by)
            except bson_errors.InvalidId:
                raise HTTPException(status_code=400, detail="Invalid creator ID")

            timestamp = get_current_iso_timestamp()
            data_dict['created_at'] = timestamp
            data_dict['updated_at'] = timestamp
            # Insert into MongoDB
            result = await self.db.audio_stories.insert_one(data_dict)

            return {"story_id": str(result.inserted_id), "file_name": story_data["file_name"], "status": "queued"}
        except PyMongoError as e:
            raise HTTPException(status_code=500, detail="Could not create audio story")
        except Exception as e:
            raise HTTPException(status_code=500, detail="An unexpected error occurred while creating the audio story")

    # Delete an audio story by ID
    async def delete_audio_story(self, story_id: str) -> bool:
        try:
            result = await self.db.audio_stories.delete_one({"_id": ObjectId(story_id)})
            if result.deleted_count == 0:
                raise HTTPException(status_code=404, detail="Audio story not found")
            return True
        except bson_errors.InvalidId:
            raise HTTPException(status_code=400, detail="Invalid audio story ID")
        except PyMongoError as e:
            raise HTTPException(status_code=500, detail="Could not delete audio story")
        except Exception as e:
            raise HTTPException(status_code=500, detail="An unexpected error occurred while deleting the audio story")

    # Mark an audio story as ready with metadata
    async def mark_ready(self, channel_id: str, file_path: str, meta_info: dict) -> bool:
       try:
           await self.db.audio_stories.update_one(
               {"channel_id": channel_id, "file_path": file_path},
               {
                   "$set": {
                       "is_ready": True,
                       "meta_details": meta_info,
                       "updated_at": get_current_iso_timestamp()
                   }
               }
           )

           return True
       except bson_errors.InvalidId:
              raise HTTPException(status_code=400, detail="Invalid channel ID or file path")
       except PyMongoError as e:
              raise HTTPException(status_code=500, detail="Could not update audio story as ready")
       except Exception as e:
           raise HTTPException(status_code=500, detail="Could not update audio story as ready")