# page_model.py
from pydantic import BaseModel

# Response for fetch page content
class PageResponse(BaseModel):
    success: bool
    page: str