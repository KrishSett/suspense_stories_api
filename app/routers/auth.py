from fastapi import APIRouter, HTTPException
from app.models import LoginRequest, TokenRefreshRequest
from common.password_utils import PasswordHasher
from auth.jwt_auth import JWTAuth
from app.services import AdminService
import base64
from config import config

apiRouter = APIRouter(
    prefix="/auth",
    tags=['auth']
)

jwt_auth = JWTAuth()
password_hash = PasswordHasher()
admin_service = AdminService()

@apiRouter.post("/admin")
async def login(data: LoginRequest):
    try:
        if data.type.strip().lower() != "admin":
            raise HTTPException(status_code=403, detail="Unauthorized")

        admin = await admin_service.find_admin_with_email(data.email)

        if not admin or not password_hash.verify(data.password, admin["password_hash"]):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        access_token = await jwt_auth.create_access_token({
            "id": admin["objectId"],
            "sub": admin["email"],
            "role": "admin"
        })
        refresh_auth_token = await jwt_auth.create_refresh_token({
            "id": admin["objectId"],
            "sub": admin["email"],
            "role": "admin"
        })

        encoded_refresh_token = base64.b64encode(refresh_auth_token.encode('ascii'))

        return {
            "success": True,
            "access_token": access_token,
            "refresh_token": encoded_refresh_token,
            "expires_in": config["token_expiry"] * 60
        }

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Internal Server Error")


@apiRouter.post("/token/refresh")
async def refresh_token(data: TokenRefreshRequest):
    try:
        payload = await jwt_auth.decode_refresh_token(data.refresh_token)
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

        new_access_token = await jwt_auth.create_access_token({
            "id": payload.get("id"),
            "sub": payload.get("sub"),
            "role": payload.get("role", "admin")
        })

        return {
            "success": True,
            "access_token": new_access_token,
            "token_type": "bearer",
            "expires_in": config["token_expiry"] * 60
        }

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
