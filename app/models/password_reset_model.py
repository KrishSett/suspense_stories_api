# password_reset_model.py
from pydantic import BaseModel, EmailStr, constr
from typing import Literal

# Request model for initiating a password reset
class ForgotPasswordRequest(BaseModel):
    email: EmailStr
    type: Literal["admin", "user"]

# Model for resetting the password
class PasswordResetRequest(BaseModel):
    reset_token: str
    new_password: constr(min_length=8, max_length=128)
    confirm_password: constr(min_length=8, max_length=128)

# Response for forgot password request
class PasswordResetResponse(BaseModel):
    success: bool
    message: str
    result: dict