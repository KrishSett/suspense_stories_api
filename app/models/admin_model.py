# admin_model.py
from pydantic import BaseModel, EmailStr

# Base admin model
class AdminBase(BaseModel):
    firstname: str
    lastname: str
    email: EmailStr

# Admin create model
class AdminCreate(AdminBase):
    password_hash: str

# Admin list model
class AdminList(AdminBase):
    pass