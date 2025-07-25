import logging
import os
from config import config

LOG_FILE = config["log_file_name"]

# Create file if it doesn't exist
if not os.path.exists(LOG_FILE):
    open(LOG_FILE, 'a').close()

# Set up root logger (not uvicorn.*)
logger = logging.getLogger("custom_logger")
logger.setLevel(logging.INFO)

if not logger.handlers:
    file_handler = logging.FileHandler(LOG_FILE)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
