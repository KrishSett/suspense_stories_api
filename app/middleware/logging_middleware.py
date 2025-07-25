from fastapi import Request
from fastapi.responses import JSONResponse, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from logging import Logger
import traceback
import json

class LoggingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, logger: Logger):
        super().__init__(app)
        self.logger = logger

    async def dispatch(self, request: Request, call_next):
        body_bytes = await request.body()
        try:
            json_body = json.loads(body_bytes)
            body = json.dumps(json_body, separators=(",", ":"), ensure_ascii=False)
        except (json.JSONDecodeError, UnicodeDecodeError):
            body = body_bytes.decode("utf-8", errors="ignore")

        self.logger.info(f"[REQUEST] {request.method} {request.url} - {str(body)}")

        try:
            # Capture the response
            response = await call_next(request)

            # Read and log response body
            response_body = b""
            async for chunk in response.body_iterator:
                response_body += chunk

            # Clone the response so FastAPI can send it again
            new_response = Response(
                content=response_body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type
            )

            self.logger.info(f"[RESPONSE] {request.method} {request.url} - {response.status_code} - {response_body.decode('utf-8')}")
            return new_response
        except Exception as e:
            # Log the exception but DO NOT suppress it
            self.logger.error(f"[MIDDLEWARE] Exception in request: {e}\n{traceback.format_exc()}")
            raise Exception(f"Error {e}")
