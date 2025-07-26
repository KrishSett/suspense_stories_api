#  helpers.py
def get_current_iso_timestamp() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()

def generate_unique_id() -> str:
    import uuid
    return str(uuid.uuid4())