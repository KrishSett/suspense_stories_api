from motor.motor_asyncio import AsyncIOMotorClient
from config import config

# Initialize MongoDB client and database
client = AsyncIOMotorClient(config['mongo_url'])
db = client[config["mongo_db"]]
