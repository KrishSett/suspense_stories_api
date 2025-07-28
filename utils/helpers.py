#  helpers.py
from datetime import datetime, timezone
import time, uuid, re
from jose import jwt, JWTError, ExpiredSignatureError
from config import config
from fastapi import HTTPException

def get_current_iso_timestamp() -> datetime:
    return datetime.now(timezone.utc)

def generate_unique_id() -> str:
    import uuid
    return str(uuid.uuid4())

def process_cache_key(key: str):
    return key.lower().replace(" ", "_").replace("-", "_")

def sanitize_filename(filename: str) -> str:
    # remove ../ and special chars for safety
    return re.sub(r"[^a-zA-Z0-9_\-.]", "", filename)

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
