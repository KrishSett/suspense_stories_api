from pydantic import BaseModel, ConfigDict
from bson import ObjectId
from typing import Any

# Custom ObjectId type (for Pydantic v2)
class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v: Any):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, core_schema, handler):
        schema = handler(core_schema)
        schema.update(type="string", examples=["64a8e4f6a1c4f2bb20c9bde0"])
        return schema

# Common base model for all MongoDB models
class MongoBaseModel(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,  # allow field aliasing (e.g., _id to id)
        arbitrary_types_allowed=True,  # allow ObjectId
        from_attributes=True  # useful if ORM-like use or response parsing
    )
