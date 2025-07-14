# admin_services.py

from app.db.conn import db

def list_admin():
    admins = db.admins.find({}, {"_id": 0})
    return list(admins)

