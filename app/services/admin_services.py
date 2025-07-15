# admin_services.py
from db import db

def list_admin():
    admins = db.admins.find(
        {"is_active": True},
        {"_id": 0, "firstname": 1, "lastname": 1, "email": 1}
    )
    return admins

