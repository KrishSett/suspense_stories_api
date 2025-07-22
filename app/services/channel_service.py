# channel_service.py
from fastapi import HTTPException
from pymongo.errors import PyMongoError
from app.models import ChannelCreate, ChannelList
from app.services.base_service import BaseService
from bson import ObjectId

class ChannelService(BaseService):
    def __init__(self):
        super().__init__()

    # Create a new channel
    async def create_channel(self, channel_data: ChannelCreate, created_by) -> ChannelList:
        try:
            # Convert to dict, exclude None values
            data_dict = channel_data.dict(exclude_none=True, by_alias=True)

            # Convert created_by to ObjectId
            data_dict["created_by"] = ObjectId(created_by)

            # Insert into MongoDB
            result = await self.db.channels.insert_one(data_dict)

            return {"_id": str(result.inserted_id)}

        except PyMongoError as e:
            print(f"Database error: {e}")
            raise HTTPException(status_code=500, detail="Could not create channel")


