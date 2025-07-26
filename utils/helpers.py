#  helpers.py
from datetime import datetime, timezone

def get_current_iso_timestamp() -> datetime:
    return datetime.now(timezone.utc)

def generate_unique_id() -> str:
    import uuid
    return str(uuid.uuid4())