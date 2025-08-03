from fastapi import APIRouter, HTTPException, BackgroundTasks
from app.models import LoginRequest, SignupRequest, TokenRefreshRequest, AccessTokenResponse, RefreshTokenResponse
from common.access_tokens import AccessTokenManager
from common.password_utils import PasswordHasher
from app.services import AdminService, UserService
from config import config
from common import RedisHashCache
from utils.helpers import process_cache_key
from app.notifications import EmailVerificationNotification
import uuid

authRouter = APIRouter(
    prefix="/auth",
    tags=['auth']
)

# Instantiate services and utilities
# These should be instantiated once to avoid multiple unnecessary initializations
access_token_manager = AccessTokenManager()
password_hash = PasswordHasher()
admin_service = AdminService()
user_service = UserService()
cache = RedisHashCache(prefix=config["cache_prefix"])
email_notification = EmailVerificationNotification()

# Admin login endpoint
@authRouter.post("/admin", response_model=AccessTokenResponse)
async def login(data: LoginRequest):
    try:
        if data.type.strip().lower() != "admin":
            raise HTTPException(status_code=403, detail="Unauthorized")

        admin = await admin_service.find_admin_with_email(data.email)

        if not admin or not password_hash.verify(data.password, admin["password_hash"]):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        # Create access and refresh tokens for the admin
        token_response = await access_token_manager.generate_tokens(user_id=admin["objectId"], user_email=admin["email"], role="admin")
        return token_response
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Internal Server Error")

# User signup  endpoint
@authRouter.post("/user/signup", response_model=AccessTokenResponse)
async def user_signup(data: SignupRequest, background_tasks: BackgroundTasks):
    try:
        if data.type.strip().lower() != "user":
            raise HTTPException(status_code=403, detail="Unauthorized")

        hashed_password = password_hash.hash(data.password)
        verification_token = str(uuid.uuid4())

        # Create a new user object
        new_user = {
            "firstname": data.firstname,
            "lastname": data.lastname,
            "email": data.email,
            "password_hash": hashed_password,
            "phone": data.phone,
            "role": "user",
            "is_active": True,
            "favorite_channels": [],
            "playlist": [],
            "is_verified": False,
            "verification_token": verification_token,
            "created_at": None,
            "updated_at": None
        }

        created_user = await user_service.create_user(new_user)

        if not created_user:
            raise HTTPException(status_code=500, detail="Could not create user")

        # Create access and refresh tokens for the new user
        token_response = await access_token_manager.generate_tokens(user_id=created_user["objectId"], user_email=created_user["email"], role="user")

        # Send email verification in the background
        background_tasks.add_task(email_notification.notify, created_user["email"], verification_token)

        if not token_response:
            raise HTTPException(status_code=500, detail="Could not generate tokens")
        else:
            # Delete cache for active channels
            cache_key = process_cache_key()
            await cache.h_del_wildcard(cache_key, "list_users")

        return token_response
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Internal Server Error")

# Email verification endpoint
@authRouter.get("/verify-email/{token}")
async def verify_email(token: str):
    user = await user_service.find_by_verification_token(token)

    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    await user_service.update_user(
        user_id=user["_id"],
        update_data={"is_verified": True, "verification_token": None}
    )

    return {"message": "Email verified successfully"}

# User login  endpoint
@authRouter.post("/user", response_model=AccessTokenResponse)
async def user_login(data: LoginRequest):
    try:
        if data.type.strip().lower() != "user":
            raise HTTPException(status_code=403, detail="Unauthorized")

        user = await user_service.find_user_with_email(data.email)

        # Check if user exists and password matches
        if not user or not password_hash.verify(data.password, user["password_hash"]):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        # Check if user email is verified
        if not user["is_verified"]:
            raise HTTPException(status_code=403, detail="Email not verified")

        # Create access and refresh tokens for the user
        token_response = await access_token_manager.generate_tokens(user_id=user["objectId"], user_email=user["email"], role="user")
        return token_response
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Internal Server Error")



# Refresh token endpoint
@authRouter.post("/token/refresh", response_model=RefreshTokenResponse)
async def refresh_token(data: TokenRefreshRequest):
    try:
        # Verify the refresh token and generate new access token
        new_access_token = await access_token_manager.refresh_access_token(data.refresh_token)
        return new_access_token
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
