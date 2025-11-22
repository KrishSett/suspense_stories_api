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

    # Create an access token with the given data and optional expiry.
    async def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        to_encode = data.copy()
        expire = datetime.utcnow() + (expires_delta or timedelta(minutes=self.token_expiry))
        to_encode.update({"exp": expire, "type": "access"})
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

    # Create a refresh token with the given data and optional expiry based on remember me token.
    async def create_refresh_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        to_encode = data.copy()

        if expires_delta is None:
            expires_delta = timedelta(days=self.refresh_token_expire_days)

        expire = datetime.utcnow() + expires_delta
        to_encode.update({"exp": expire, "type": "refresh"})
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

    # Verify the given token and return its payload if valid.
    async def verify_token(self, token: str) -> Optional[dict]:
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except JWTError:
            return None

    # Decode and verify a refresh token specifically.
    async def decode_refresh_token(self, token: str) -> Optional[dict]:
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            if payload.get("type") != "refresh":
                raise JWTError("Invalid token type")
            return payload
        except JWTError:
            return None
