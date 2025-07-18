from fastapi import APIRouter, HTTPException
from app.models import LoginRequest, TokenRefreshRequest
from common.password_utils import PasswordHasher
from auth.jwt_auth import JWTAuth
from app.services import AdminService

apiRouter = APIRouter(
    prefix="/auth",
    tags=['auth']
)

jwt_auth = JWTAuth()
password_hash = PasswordHasher()
admin_service = AdminService()

@apiRouter.post("/admin")
async def login(form: LoginRequest):
    try:
        if form.type != "admin":
            raise HTTPException(status_code=403, detail="Unauthorized")

        admin = await admin_service.find_admin_with_email(form.email)

        if not admin or not password_hash.verify(form.password, admin["password_hash"]):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        access_token = await jwt_auth.create_access_token({"sub": form.email, "role": "admin"})
        refresh_token = await jwt_auth.create_refresh_token({"sub": form.email, "role": "admin"})

        return {
            "success": True,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": 3600
        }

    except HTTPException:
        raise  # re-raise custom exceptions
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error")


@apiRouter.post("/token/refresh")
async def refresh_token(request: TokenRefreshRequest):
    try:
        payload = await jwt_auth.decode_refresh_token(request.refresh_token)
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

        # optionally issue a new access token
        new_access_token = await jwt_auth.create_access_token({
            "sub": payload.get("sub"),
            "role": payload.get("role", "admin")
        })

        return {
            "success": True,
            "access_token": new_access_token,
            "token_type": "bearer",
            "expires_in": 3600
        }

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
