from fastapi import Header, HTTPException
from auth.jwt_auth import JWTAuth

class JWTAuthGuard:
    def __init__(self, expected_role: str):
        self.expected_role = expected_role

    async def __call__(self, authorization: str = Header(...)):
        if not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid token format")

        token = authorization.split(" ")[1]
        jwt = JWTAuth()

        try:
            payload = await jwt.verify_token(token)  # assuming this is async
        except Exception:
            raise HTTPException(status_code=401, detail="Invalid or expired token")

        if not payload:
            raise HTTPException(status_code=401, detail="Invalid or expired token")

        role = payload.get("role")
        if role != self.expected_role:
            raise HTTPException(status_code=403, detail=f"{self.expected_role.capitalize()}s only")

        return payload["sub"]  # or return payload if you need more
