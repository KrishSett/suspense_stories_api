# main.py

from typing import Union
from fastapi import FastAPI
from app.routers import adminRouter

app = FastAPI(
    docs_url=None,         # disables Swagger UI at /docs
    redoc_url=None,        # disables ReDoc at /redoc
    openapi_url=None       # disables the OpenAPI JSON at /openapi.json
)

app.include_router(adminRouter)
