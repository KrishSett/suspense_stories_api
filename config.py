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
app_name = os.getenv("APP_NAME", "APP Name")
mongo_url = os.getenv("MONGO_URL")
mongo_db = os.getenv("MONGO_DB")
secret_key = os.getenv("SECRET_KEY")
algorithm = os.getenv("ALGORITHM", "HS256")
token_expiry = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 15))
refresh_token_expire_days = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 7))
log_file_name = os.getenv("LOG_FILE_NAME", "app.log")
mail_mailer = os.getenv("MAIL_MAILER")
mail_host = os.getenv("MAIL_HOST")
mail_port = int(os.getenv("MAIL_PORT"))
mail_username = os.getenv("MAIL_USERNAME", "app.log")
mail_password = os.getenv("MAIL_PASSWORD", "app.log")
mail_from = os.getenv("MAIL_FROM", "app.log")
file_download_dir = os.getenv("FILE_DOWNLOAD_DIR", "downloads")
ffmpeg_path = os.getenv("FFMPEG_PATH")

if not mongo_url or not mongo_db:
    raise EnvironmentError("Missing critical environment variables: MONGO_URL or MONGO_DB.")

# Return config as a dictionary
config = {
    "app_name": app_name,
    "mongo_url": mongo_url,
    "mongo_db": mongo_db,
    "secret_key": secret_key,
    "algorithm": algorithm,
    "token_expiry": token_expiry,
    "refresh_token_expire_days": refresh_token_expire_days,
    "log_file_name": log_file_name,
    "mail_mailer": mail_mailer,
    "mail_host": mail_host,
    "mail_port": mail_port,
    "mail_username": mail_username,
    "mail_password": mail_password,
    "mail_from": mail_from,
    "file_download_dir": file_download_dir,
    "ffmpeg_path": ffmpeg_path
}
