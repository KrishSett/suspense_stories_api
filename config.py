# config.py
import os
from pathlib import Path
from dotenv import load_dotenv

# Define path to .env file
env_path = Path(__file__).parent / ".env"

# Check existence before loading
if not env_path.exists():
    raise FileNotFoundError(".env file not found at:", env_path)

load_dotenv(dotenv_path=env_path)

# Access and validate required variables
mongo_url = os.getenv("MONGO_URL")
mongo_db = os.getenv("MONGO_DB")

if not mongo_url or not mongo_db:
    raise EnvironmentError("Missing critical environment variables: MONGO_URL or MONGO_DB.")

# Return config as a dictionary
config = {
    "mongo_url": mongo_url,
    "mongo_db": mongo_db
}
