# base_service.py
from db import db  # your MongoDB connection setup

class BaseService:
    def __init__(self):
        self.db = db
