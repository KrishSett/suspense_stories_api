# base_service.py
from db import db  # your MongoDB connection setup
import logging
import os

class BaseService:
    def __init__(self):
        self.db = db

        log_format = (
            "%(asctime)s | %(levelname)s | %(filename)s:%(funcName)s:%(lineno)d | %(message)s"
        )

        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)

        logging.basicConfig(
            level=logging.INFO,
            format=log_format,
            handlers=[
                logging.FileHandler(os.path.join(log_dir, "app.log")),
                logging.StreamHandler(),
            ],
        )

        self.logger = logging.getLogger(self.__class__.__name__)
