from datetime import datetime, timezone

def get_current_iso_timestamp() -> datetime:
    return datetime.now(timezone.utc)