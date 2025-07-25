# main.py
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from logging_setup import logger
import traceback
from app.middleware.logging_middleware import LoggingMiddleware
from app.routers import adminRouter, authRouter
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

# Initialize FastAPI app with docs disabled
app = FastAPI(
    docs_url=None,
    redoc_url=None,
    openapi_url=None
)

# Add middleware and routers
app.add_middleware(LoggingMiddleware, logger=logger)
app.include_router(authRouter)
app.include_router(adminRouter)

# Global error handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    tb = traceback.format_exc()
    logger.error(f"[UNHANDLED EXCEPTION] {request.method} {request.url} | {exc}\n{tb}")

    return JSONResponse(
        status_code=500,
        content={
            "error": str(exc),
            "trace": tb
        }
    )

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    logger.warning(f"[HTTP ERROR] {request.method} {request.url} | {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning(f"[VALIDATION ERROR] {request.method} {request.url} | {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()}
    )
