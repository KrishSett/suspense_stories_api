#  helpers.py
from datetime import datetime, timezone, timedelta
import time, uuid, re
from jose import jwt, JWTError, ExpiredSignatureError
from config import config
from fastapi import HTTPException
from urllib.parse import quote_plus

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

# Generate a secure verification token
def generate_verification_token() -> str:
    import secrets
    return secrets.token_urlsafe(32)

# Generate an expiry time in ISO format, defaulting to 5 minutes from now
def generate_expiry_time(minutes: int = 5) -> str:
    expiry_time = datetime.utcnow() + timedelta(minutes=minutes)
    return expiry_time.isoformat()

# Generate a placeholder image URL
def generate_placeholder_img(text, width=75, height=75, bg_color="e5d5f7", text_color="77878"):
    # Default text if empty
    if not len(text):
        text = "N/A"

    # Encode text safely for URL
    encoded_text = quote_plus(text)

    url = f"https://placehold.co/{width}x{height}/{bg_color}/{text_color}?text={encoded_text}&font=poppins"
    return url