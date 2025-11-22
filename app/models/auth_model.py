# auth_model.py
from pydantic import BaseModel, EmailStr
from typing import Literal

# Login request model
class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    type: Literal["admin", "user"]
    remember_me: bool = False

# Signup request model
class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    firstname: str
    lastname: str
    phone: str = None
    type: Literal["user"] # for now only user can signup
    tnc: bool

# Refresh token model
class TokenRefreshRequest(BaseModel):
    refresh_token: str

# Access token response model
class AccessTokenResponse(BaseModel):
    success: bool
    access_token: str
    refresh_token: str
    expires_in: int

# Refresh token response model
class RefreshTokenResponse(BaseModel):
    success: bool
    access_token: str
    type: Literal["bearer"]
    expires_in: int

# Verify email response model
class VerifyEmailResponse(BaseModel):
    success: bool
    message: str