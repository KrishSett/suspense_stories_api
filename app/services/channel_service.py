# channel_service.py
from typing import Optional
from fastapi import HTTPException
from pymongo.errors import PyMongoError
from bson import ObjectId, errors as bson_errors
from app.services.base_service import BaseService
from utils.helpers import get_current_iso_timestamp

class ChannelService(BaseService):
    def __init__(self):
        super().__init__()

    # List all active channels
    async def list_active_channels(self) -> Optional[list]:
        try:
            channels = self.db.channels.find(
                {"is_active": True},
                {"_id": 0, "youtube_channel_id": 1, "title": 1, "created_at": 1, "order_position": 1}
            )
            result = await channels.to_list(length=None)
            self.logger.info("Fetched %d active channels", len(result))
            return result
        except PyMongoError as e:
            self.logger.error("Error in %s: %s", "list_active_channels", e)
            raise HTTPException(status_code=500, detail="Could not fetch channel data")

    # Find a channel by its ID
    async def find_channel_by_id(self, channel_id: str) -> Optional[dict]:
        try:
            channel = await self.db.channels.find_one(
                {"_id": ObjectId(channel_id), "is_active": True},
                {"_id": 0, "youtube_channel_id": 1, "title": 1, "created_at": 1, "order_position": 1}
            )
            if channel:
                self.logger.info("Channel found for ID %s", channel_id)
                return channel
            else:
                self.logger.warning("Channel not found for ID %s", channel_id)
                raise HTTPException(status_code=404, detail="Channel not found")
        except bson_errors.InvalidId:
            self.logger.warning("Invalid channel ID provided: %s", channel_id)
            raise HTTPException(status_code=400, detail="Invalid channel ID")
        except PyMongoError as e:
            self.logger.error("Error in %s for ID %s: %s", "find_channel_by_id", channel_id, e)
            raise HTTPException(status_code=500, detail="Could not fetch channel data")

    # Create a new channel
    async def create_channel(self, channel_data: dict, created_by: str) -> Optional[dict]:
        try:
            data_dict = channel_data
            try:
                data_dict["created_by"] = ObjectId(created_by)
            except bson_errors.InvalidId:
                self.logger.warning("Invalid creator ID: %s", created_by)
                raise HTTPException(status_code=400, detail="Invalid creator ID")

            timestamp = get_current_iso_timestamp()
            data_dict["created_at"] = timestamp
            data_dict["updated_at"] = timestamp

            result = await self.db.channels.insert_one(data_dict)
            self.logger.info("Channel created successfully with ID %s", str(result.inserted_id))
            return {"channel_id": str(result.inserted_id), "created_at": timestamp, "status": True}
        except PyMongoError as e:
            self.logger.error("Error in %s for channel %s: %s", "create_channel", channel_data.get("title"), e)
            raise HTTPException(status_code=500, detail="Could not create channel")

    # Update an existing channel
    async def update_channel(self, channel_id: str, update_data: dict) -> Optional[dict]:
        try:
            update_data["updated_at"] = get_current_iso_timestamp()
            result = await self.db.channels.update_one(
                {"_id": ObjectId(channel_id)},
                {"$set": update_data}
            )

            if result.modified_count == 0:
                self.logger.warning("No channel updated for ID %s", channel_id)
                raise HTTPException(status_code=404, detail="Channel not found or no changes made")

            self.logger.info("Channel updated successfully for ID %s", channel_id)
            return {"status": True, "message": "Channel updated successfully"}
        except bson_errors.InvalidId:
            self.logger.warning("Invalid channel ID for update: %s", channel_id)
            raise HTTPException(status_code=400, detail="Invalid channel ID")
        except PyMongoError as e:
            self.logger.error("Error in %s for ID %s: %s", "update_channel", channel_id, e)
            raise HTTPException(status_code=500, detail="Could not update channel")

    # Set the order position of a channel
    async def set_channel_order(self, channel_id: str, order_position: int) -> Optional[dict]:
        try:
            current_channel = await self.db.channels.find_one({"_id": ObjectId(channel_id)})
            if not current_channel:
                self.logger.warning("Channel not found for ID %s", channel_id)
                raise HTTPException(status_code=404, detail="Channel not found")

            current_position = current_channel.get("order_position", None)

            if current_position == order_position:
                self.logger.info("No changes needed for channel ID %s", channel_id)
                return {"status": True, "message": "No changes needed"}

            await self.db.channels.update_many(
                {"order_position": {"$gte": order_position}},
                {"$inc": {"order_position": 1}}
            )

            result = await self.db.channels.update_one(
                {"_id": ObjectId(channel_id)},
                {
                    "$set": {
                        "order_position": order_position,
                        "updated_at": get_current_iso_timestamp(),
                    }
                }
            )

            if result.modified_count == 0:
                self.logger.warning("No channel order updated for ID %s", channel_id)
                raise HTTPException(status_code=404, detail="No changes made")

            self.logger.info("Channel order updated successfully for ID %s", channel_id)
            return {"status": True, "message": "Channel order position updated successfully"}
        except bson_errors.InvalidId:
            self.logger.warning("Invalid channel ID for set order: %s", channel_id)
            raise HTTPException(status_code=400, detail="Invalid channel ID")
        except PyMongoError as e:
            self.logger.error("Error in %s for ID %s: %s", "set_channel_order", channel_id, e)
            raise HTTPException(status_code=500, detail="Could not update channel order position")
