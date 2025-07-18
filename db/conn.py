import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from config import config

client = AsyncIOMotorClient(config['mongo_url'])
db = client[config["mongo_db"]]
