# auth_model.py
from pydantic import BaseModel, EmailStr
from typing import Literal

# Login request model
class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    type: Literal["admin", "user"]

# Signup request model
class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    firstname: str
    lastname: str
    phone: str = None
    type: Literal["user"] # for now only user can signup

# Refresh token model
class TokenRefreshRequest(BaseModel):
    refresh_token: str

# Access token response model
class AccessTokenResponse(BaseModel):
    success: bool
    access_token: str
    refresh_token: str
    expires_in: int

class RefreshTokenResponse(BaseModel):
    success: bool
    access_token: str
    type: Literal["bearer"]
    expires_in: int