# user_model.py
from pydantic import BaseModel, EmailStr

# Base user model
class UserBase(BaseModel):
    firstname: str
    lastname: str
    email: EmailStr

# User list  model
class UserList(UserBase):
    is_active: bool = True