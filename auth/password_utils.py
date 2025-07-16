from passlib.context import CryptContext
from passlib.exc import UnknownHashError
from fastapi import HTTPException

class PasswordHasher:
    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def hash(self, password: str) -> str:
        return self.pwd_context.hash(password)

    def verify(self, plain_password: str, hashed_password: str) -> bool:
        try:
            return self.pwd_context.verify(plain_password, hashed_password)
        except UnknownHashError:
            raise HTTPException(
                status_code=400,
                detail="Invalid password hash format"
            )
