# conn.py
from pymongo import MongoClient
from config import config

client = MongoClient(config['mongo_url'])

# Check connection
try:
    client.admin.command("ping")
except Exception as e:
    raise ConnectionError(f"Failed to connect to MongoDB: {e}")

db = client[config["mongo_db"]]