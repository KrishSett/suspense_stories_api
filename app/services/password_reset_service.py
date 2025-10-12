# password_reset_service.py
from fastapi import HTTPException
from datetime import datetime
from pymongo.errors import PyMongoError
from bson import ObjectId, errors as bson_errors
from app.services.base_service import BaseService
from utils.helpers import get_current_iso_timestamp, generate_verification_token, generate_expiry_time

class PasswordResetService(BaseService):
    def __init__(self):
        super().__init__()

    # Create a password reset token for a user or admin
    async def create_password_reset_token(self, resource_id: str, user_type: str, email: str) -> str | None:
        try:
            if user_type not in ("admin", "user"):
                self.logger.error("Invalid user type provided: %s", user_type)
                raise HTTPException(status_code=400, detail="Invalid user type")

            existing_token = await self.is_valid_reset_token(resource_id=resource_id)

            if existing_token is not None:
                return existing_token

            timestamp = get_current_iso_timestamp()
            reset_token = generate_verification_token()
            expiry_time = generate_expiry_time(60)  # 60 minutes

            # Insert the reset token document
            insert_result = await self.db.password_resets.insert_one({
                    "resource_id": ObjectId(resource_id),
                    "user_type": user_type,
                    "is_active": True,
                    "reset_token": reset_token,
                    "email": email,
                    "reset_token_expiry": datetime.fromisoformat(expiry_time),
                    "created_at": timestamp,
                    "updated_at": timestamp
                })

            if insert_result.inserted_id:
                self.logger.info("Password reset token created for user_id: %s", resource_id)
                return reset_token
            else:
                self.logger.error("Failed to create password reset token for user_id: %s", resource_id)
                return None

        except PyMongoError as e:
            self.logger.error("Database error while creating password reset token: %s", str(e))
            raise HTTPException(status_code=500, detail="Internal Server Error" + str(e))
        except Exception as e:
            self.logger.error("Unexpected error while creating password reset token: %s", str(e))
            raise HTTPException(status_code=500, detail="Internal Server Error")

    # Validate and retrieve the password reset token
    async def is_valid_reset_token(self, resource_id: str) -> str | None:
        try:
            current_time = datetime.utcnow()
            token_doc = await self.db.password_resets.find_one({
                "resource_id": ObjectId(resource_id),
                "is_active": True,
                "reset_token_expiry": {"$gt": current_time}
            }, {
                "reset_token": 1
            })

            if token_doc:
                self.logger.info("Valid password reset token for resource id: %s", resource_id)
                return token_doc["reset_token"]
            else:
                self.logger.warning("Invalid or expired password reset token for resource id: %s", resource_id)
                return None

        except PyMongoError as e:
            self.logger.error("Database error while validating reset token: %s", str(e))
            raise HTTPException(status_code=500, detail="Internal Server Error")
        except Exception as e:
            self.logger.error("Unexpected error while validating reset token: %s", str(e))
            raise HTTPException(status_code=500, detail="Internal Server Error")

    # Find the password reset record by reset token
    async def find_reset_record(self, reset_token: str) -> dict | None:
        try:
            record = await self.db.password_resets.find_one({
                "reset_token": reset_token,
                "is_active": True,
                "reset_token_expiry": {"$gt": datetime.utcnow()}
            }, {
                "_id": 0, "resource_id": 1, "user_type": 1, "email": 1
            })

            if record:
                self.logger.info("Password reset record found for token: %s", reset_token)
                return record
            else:
                self.logger.warning("No valid password reset record found for token: %s", reset_token)
                return None

        except PyMongoError as e:
            self.logger.error("Database error while fetching reset record: %s", str(e))
            raise HTTPException(status_code=500, detail="Internal Server Error")
        except Exception as e:
            self.logger.error("Unexpected error while fetching reset record: %s", str(e))
            raise HTTPException(status_code=500, detail="Internal Server Error")

    # Reset the user's or admin's password using the reset token
    async def reset_password(self, reset_token: str, new_password_hash: str) -> dict | None:
        try:
            record = await self.find_reset_record(reset_token=reset_token)
            if record is None:
                self.logger.warning("Invalid or expired password reset token: %s", reset_token)
                return None

            resource_id = record["resource_id"]
            user_type = record["user_type"]
            email = record["email"]

            if user_type == "admin":
                collection = self.db.admins
            elif user_type == "user":
                collection = self.db.users
            else:
                self.logger.error("Invalid user type in reset record: %s", user_type)
                raise HTTPException(status_code=400, detail="Invalid user type in reset record")

            # Update the password in the respective collection
            update_result = await collection.update_one(
                {"_id": ObjectId(resource_id), "is_active": True, "email": email},
                {"$set": {"password_hash": new_password_hash, "updated_at": get_current_iso_timestamp()}}
            )

            # Invalidate the reset token
            await self.db.password_resets.update_one(
                {"reset_token": reset_token},
                {"$set": {"is_active": False, "updated_at": get_current_iso_timestamp()}}
            )

            if update_result.modified_count == 1:
                self.logger.info("Password successfully reset using token: %s", reset_token)
                return {
                    "email": email,
                    "user_type": user_type
                }
            else:
                self.logger.warning("Invalid or expired password reset token: %s", reset_token)
                return None
        except PyMongoError as e:
            self.logger.error("Database error while resetting password: %s", str(e))
            raise HTTPException(status_code=500, detail="Internal Server Error")
        except Exception as e:
            self.logger.error("Unexpected error while resetting password: %s", str(e))
            raise HTTPException(status_code=500, detail="Internal Server Error")