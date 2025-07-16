from fastapi import Header, HTTPException, Depends
from auth.jwt_auth import JWTAuth

class JWTAuthGuard:
    def __init__(self, expected_role: str):
        self.expected_role = expected_role

    def __call__(self, authorization: str = Header(...)):
        # Check format
        if not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid token format")

        # Extract and decode token
        token = authorization.split(" ")[1]
        jwt = JWTAuth()
        payload = jwt.verify_token(token)

        if not payload:
            raise HTTPException(status_code=401, detail="Invalid or expired token")

        # Check role
        role = payload.get("role")
        if role != self.expected_role:
            raise HTTPException(status_code=403, detail=f"{self.expected_role.capitalize()}s only")

        # Return user identity (you can return entire payload if needed)
        return payload["sub"]
