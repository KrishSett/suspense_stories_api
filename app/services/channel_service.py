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

    # List active channels with pagination
    async def list_active_channels(self, page: int = 1, page_size: int = 10) -> Optional[dict]:
        try:
            skip = (page - 1) * page_size

            query = {"is_active": True}
            projection = {
                "_id": 1,
                "youtube_channel_id": 1,
                "title": 1,
                "order_position": 1,
                "thumbnail_url": 1,
                "description": 1
            }

            # Count total documents
            total_channels = await self.db.channels.count_documents(query)

            # Fetch paginated results
            cursor = (self.db.channels.find(query, projection)
                      .sort("order_position", 1)
                      .skip(skip)
                      .limit(page_size))
            result = await cursor.to_list(length=page_size)

            channels = []
            for ch in result:
                channels.append({
                    "channel_id": str(ch["_id"]),
                    "youtube_channel_id": ch["youtube_channel_id"],
                    "title": ch["title"],
                    "is_active": ch.get("is_active", True),
                    "order_position": ch["order_position"],
                    "description": ch.get("description") or "No description available",
                    "thumbnail_url": ch.get("thumbnail_url") or "https://example.com/default_thumbnail.png",
                    "status": True
                })

            self.logger.info(
                "Fetched %d active channels (page %d, page_size %d)", len(channels), page, page_size
            )

            return {
                "total": total_channels,
                "page": page,
                "page_size": page_size,
                "total_pages": (total_channels + page_size - 1) // page_size,
                "data": channels
            }

        except PyMongoError as e:
            self.logger.error("Error in %s: %s", "list_active_channels", e)
            raise HTTPException(status_code=500, detail="Could not fetch channel data")

    # Find a channel by its ID
    async def find_channel_by_id(self, channel_id: str) -> Optional[dict]:
        try:
            channel = await self.db.channels.find_one(
                {"_id": ObjectId(channel_id)},
                {
                    "_id": 1,
                    "youtube_channel_id": 1,
                    "title": 1,
                    "order_position": 1,
                    "thumbnail_url": 1,
                    "description": 1,
                    "is_active": 1,
                 }
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
            data_dict["published_at"] = timestamp

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
                raise HTTPException(status_code=404, detail="Channel not found")

            current_position = current_channel.get("order_position")

            if current_position == order_position:
                return {"status": True, "message": "No changes needed"}

            if order_position < current_position:
                # Moving UP -> Increment positions for channels in range [order_position, current_position - 1]
                await self.db.channels.update_many(
                    {"order_position": {"$gte": order_position, "$lt": current_position}},
                    {"$inc": {"order_position": 1}}
                )

            else:
                # Moving DOWN -> Decrement positions for channels in range [current_position + 1, order_position]
                await self.db.channels.update_many(
                    {"order_position": {"$gt": current_position, "$lte": order_position}},
                    {"$inc": {"order_position": -1}}
                )

            # Finally update this channel
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
                raise HTTPException(status_code=404, detail="No changes made")

            return {"status": True, "message": "Channel order position updated successfully"}

        except bson_errors.InvalidId:
            raise HTTPException(status_code=400, detail="Invalid channel ID")
        except PyMongoError as e:
            raise HTTPException(status_code=500, detail="Could not update channel order position")
