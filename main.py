# main.py

from typing import Union
from fastapi import FastAPI
from app.routers.admins import apiRouter as route_admin

app = FastAPI()
#app.include_router(route_admin)
