# access_tokens.py
from pydantic import EmailStr
from auth.jwt_auth import JWTAuth
import base64

class AccessTokenManager:
    def __init__(self):
        self.jwt_auth = JWTAuth()

    # Create a new access token for the given user ID and role.
    async def __create_access_token(self, user_id: str, user_email: EmailStr, role: str) -> str:
        return await self.jwt_auth.create_access_token({
            "id": user_id,
            "sub": user_email,
            "role": role
        })

    # Create a new refresh token for the given user ID and role.
    async def __create_refresh_token(self, user_id: str, user_email: EmailStr, role: str) -> str:
        return await self.jwt_auth.create_refresh_token({
            "id": user_id,
            "sub":user_email,
            "role": role
        })

    # Generate both access and refresh tokens for a user.
    async def generate_tokens(self, user_id: str, user_email: EmailStr, role: str) -> dict:
        if role not in ("admin", "user"):
            raise Exception("Invalid role specified. Must be 'admin' or 'user'.")

        access_token = await self.__create_access_token(user_id, user_email, role)
        refresh_token = await self.__create_refresh_token(user_id, user_email, role)
        encoded_refresh_token = base64.b64encode(refresh_token.encode('ascii'))

        return {
            "success": True,
            "access_token": access_token,
            "refresh_token": encoded_refresh_token,
            "expires_in": self.jwt_auth.token_expiry * 60  # Convert minutes to seconds
        }

    # Process a refresh token to generate a new access token.
    async def refresh_access_token(self, refresh_token: str) -> dict:
        payload = await self.jwt_auth.decode_refresh_token(refresh_token)

        if not payload:
            raise Exception("Invalid or expired refresh token")

        new_access_token = await self.__create_access_token(
            user_id=payload.get("id"),
            user_email=payload.get("sub"),
            role=payload.get("role", "admin")
        )

        return {
            "success": True,
            "access_token": new_access_token,
            "type": "bearer",
            "expires_in": self.jwt_auth.token_expiry * 60  # Convert minutes to seconds
        }