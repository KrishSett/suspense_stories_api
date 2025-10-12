#  helpers.py
from datetime import datetime, timezone, timedelta
import time, uuid, re
from jose import jwt, JWTError, ExpiredSignatureError
from config import config
from fastapi import HTTPException

# Get current ISO timestamp in UTC
def get_current_iso_timestamp() -> datetime:
    return datetime.now(timezone.utc)

# Generate a unique identifier (UUID)
def generate_unique_id() -> str:
    import uuid
    return str(uuid.uuid4())

# Process cache key to ensure it is safe for use
def process_cache_key():
    key = config.get("cache_key", "app_key")
    return key.lower().replace(" ", "_").replace("-", "_")

# Sanitize filename to remove unsafe characters
def sanitize_filename(filename: str) -> str:
    # remove ../ and special chars for safety
    return re.sub(r"[^a-zA-Z0-9_\-.]", "", filename)

# Generate a signed URL for downloading audio files
def generate_signed_url(filename: str, expiry_seconds: int = 86400) -> str:
    safe_filename = sanitize_filename(filename)

    payload = {
        "filename": safe_filename,
        "exp": int(time.time()) + expiry_seconds
    }

    token = jwt.encode(payload, config.get("secret_key"), algorithm=config.get("algorithm", "HS256"))
    base_url = config.get("base_url", "http://localhost:8000/")

    if not base_url.endswith("/"):
        base_url += "/"

    return f"{base_url}users/audio-download/{safe_filename}?token={token}"

# Decode a signed URL token to retrieve the filename and expiration
def decode_signed_url_token(token: str) -> dict:
    try:
        payload = jwt.decode(
            token,
            config.get("secret_key"),
            algorithms=[config.get("algorithm", "HS256")]
        )
        return payload
    except ExpiredSignatureError:
        raise HTTPException(status_code=403, detail="URL expired")
    except JWTError:
        raise HTTPException(status_code=403, detail="Invalid token")

def generate_verification_token() -> str:
    import secrets
    return secrets.token_urlsafe(32)

from datetime import datetime, timedelta

def generate_expiry_time(minutes: int = 5) -> str:
    expiry_time = datetime.utcnow() + timedelta(minutes=minutes)
    return expiry_time.isoformat()