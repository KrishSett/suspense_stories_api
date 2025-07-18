from datetime import datetime, timedelta
from jose import jwt, JWTError
from typing import Optional
from config import config

class JWTAuth:
    def __init__(self):
        self.secret_key = config["secret_key"]
        self.algorithm = config["algorithm"]
        self.token_expiry = config["token_expiry"]
        self.refresh_token_expire_days = config["refresh_token_expire_days"]

    async def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        to_encode = data.copy()
        expire = datetime.utcnow() + (expires_delta or timedelta(minutes=self.token_expiry))
        to_encode.update({"exp": expire, "type": "access"})
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

    async def create_refresh_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        to_encode = data.copy()
        expire = datetime.utcnow() + (expires_delta or timedelta(days=self.refresh_token_expire_days))
        to_encode.update({"exp": expire, "type": "refresh"})
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

    async def verify_token(self, token: str) -> Optional[dict]:
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except JWTError:
            return None

    async def decode_refresh_token(self, token: str) -> Optional[dict]:
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            if payload.get("type") != "refresh":
                raise JWTError("Invalid token type")
            return payload
        except JWTError:
            return None
