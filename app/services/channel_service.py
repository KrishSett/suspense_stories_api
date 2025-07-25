from typing import Optional
from fastapi import HTTPException
from pymongo.errors import PyMongoError
from bson import ObjectId, errors as bson_errors
from app.services.base_service import BaseService
from utils.helpers import get_current_iso_timestamp

class ChannelService(BaseService):
    def __init__(self):
        super().__init__()

    async def create_channel(self, channel_data: dict, created_by: str) -> Optional[dict]:
        try:
            data_dict = channel_data

            try:
                data_dict["created_by"] = ObjectId(created_by)
            except bson_errors.InvalidId:
                raise HTTPException(status_code=400, detail="Invalid creator ID")

            timestamp = get_current_iso_timestamp()
            data_dict['created_at'] = timestamp
            data_dict['updated_at'] = timestamp

            result = await self.db.channels.insert_one(data_dict)

            return {"channel_id": str(result.inserted_id), "created_at": timestamp, "status": True}

        except PyMongoError as e:
            raise HTTPException(status_code=500, detail="Could not create channel")
