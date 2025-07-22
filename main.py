# main.py
import traceback
import logging
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.concurrency import iterate_in_threadpool
from app.routers import adminRouter, authRouter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Custom middleware for logging requests and responses
class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Log the request
        body = await request.body()
        logger.info(f"[REQUEST] {request.method} {request.url} | Body: {body.decode('utf-8')}")

        try:
            response: Response = await call_next(request)

            if "application/json" in response.headers.get("content-type", ""):
                response_body = b""
                async for chunk in response.body_iterator:
                    response_body += chunk

                # Wrap the response body back in an async iterator
                response.body_iterator = iterate_in_threadpool([response_body])

                logger.info(f"[RESPONSE] {request.method} {request.url} [{response.status_code}] | Body: {response_body.decode('utf-8')}")
            else:
                logger.info(f"[RESPONSE] {request.method} {request.url} [{response.status_code}] | Non-JSON response")

            return response

        except Exception as e:
            logger.error(f"[ERROR] {request.method} {request.url} | {str(e)}\n{traceback.format_exc()}")
            return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})


# Initialize app
app = FastAPI(
    docs_url=None,         # disables Swagger UI at /docs
    redoc_url=None,        # disables ReDoc at /redoc
    openapi_url=None       # disables the OpenAPI JSON at /openapi.json
)

# Register middleware
app.add_middleware(LoggingMiddleware)

# Register routers
app.include_router(authRouter)
app.include_router(adminRouter)

# Optional global error handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"[UNHANDLED EXCEPTION] {str(exc)}\n{traceback.format_exc()}")
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred"}
    )
