# auth.py
from fastapi import APIRouter, HTTPException
from app.models import LoginRequest
from auth.password_utils import PasswordHasher
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
def login(form: LoginRequest):

    if form.type != "admin":
        raise HTTPException(status_code=403, detail="Unauthorized, invalid admin data")

    admin = admin_service.find_admin_with_email(form.email)

    if not admin:
        raise HTTPException(status_code=404, detail="Invalid admin data")

    if not password_hash.verify(form.password, admin["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = jwt_auth.create_access_token({"sub": form.email, "role": "admin"})
    refresh_token = jwt_auth.create_refresh_token({"sub": form.email})

    return {
        "success": True,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }