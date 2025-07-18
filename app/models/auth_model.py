# auth_model.py
from pydantic import BaseModel, EmailStr
from typing import Literal

# Base auth model
class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    type: Literal["admin", "user"]

class TokenRefreshRequest(BaseModel):
    refresh_token: str
