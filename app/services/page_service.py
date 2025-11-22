# page_service.py
from fastapi import HTTPException
from pymongo.errors import PyMongoError
from app.services.base_service import BaseService

class PageService(BaseService):
    def __init__(self):
        super().__init__()

    # Get page by slug
    async def get_page_by_slug(self, slug: str) -> dict | None:
        try:
            page = await self.db.resource_pages.find_one({
                "slug": slug,
                "is_active": True
            })
            if page:
                self.logger.info("Page found with slug: %s", slug)
                return page
            else:
                self.logger.warning("No active page found with slug: %s", slug)
                return None
        except PyMongoError as e:
            self.logger.error("Database error while fetching page with slug %s: %s", slug, str(e))
            raise HTTPException(status_code=500, detail="Internal Server Error")
        except Exception as e:
            self.logger.error("Unexpected error while fetching page with slug %s: %s", slug, str(e))
            raise HTTPException(status_code=500, detail="Internal Server Error")