from fastapi import Request
from fastapi.responses import Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from logging import Logger
import traceback
import json

class LoggingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, logger: Logger):
        super().__init__(app)
        self.logger = logger
        self.exception_routes = [
            "/users/audio-download/"
        ]

    async def dispatch(self, request: Request, call_next):
        if request.url.path in self.exception_routes:
            return await call_next(request)

        # Log request body
        body_bytes = await request.body()
        try:
            json_body = json.loads(body_bytes)
            body = json.dumps(json_body, separators=(",", ":"), ensure_ascii=False)
        except (json.JSONDecodeError, UnicodeDecodeError):
            body = body_bytes.decode("utf-8", errors="ignore")

        self.logger.info(f"[REQUEST] {request.method} {request.url} - {body}")

        try:
            # 🔹 Get Response
            response = await call_next(request)

            # Read response body safely
            response_body = b""
            async for chunk in response.body_iterator:
                response_body += chunk

            # Create a new response so FastAPI can send it again
            new_response = Response(
                content=response_body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type
            )

            try:
                decoded_body = response_body.decode("utf-8")
            except UnicodeDecodeError:
                decoded_body = "<BINARY DATA>"

            self.logger.info(
                f"[RESPONSE] {request.method} {request.url} - "
                f"{response.status_code} - {decoded_body}"
            )

            return new_response

        except Exception as e:
            self.logger.error(
                f"[MIDDLEWARE] Exception in request: {e}\n{traceback.format_exc()}"
            )
            raise
