# auth_model.py
from pydantic import BaseModel, EmailStr, Field
from typing import Literal

# Login request model
class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    type: Literal["admin", "user"]

# Refresh token model
class TokenRefreshRequest(BaseModel):
    refresh_token: str
