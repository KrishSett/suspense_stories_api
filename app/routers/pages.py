# pages.py
from fastapi import APIRouter, HTTPException
from app.models import PageResponse
from app.services import PageService
from common import RedisHashCache
from config import config
from utils.helpers import process_cache_key

pageRouter = APIRouter(prefix="/page", tags=["page"])
page_service = PageService()
cache = RedisHashCache(prefix=config["cache_prefix"])

# Get page content with slug
@pageRouter.get("/{slug}", response_model=PageResponse)
async def get_page_content(slug: str):
    try:
        cache_key = process_cache_key()

        # Check cache
        cached_page = await cache.h_get(cache_key, "resource_pages", {"slug": slug})
        if cached_page is not None:
            return cached_page

        # Fetch active page with slug
        page = await page_service.get_page_by_slug(slug)
        if not page:
            raise HTTPException(status_code=404, detail="Page not found")

        page_content = {
            "success": True,
            "page": page.get("content", "")
        }

        # Set page content in cache
        await cache.h_set(cache_key, "resource_pages", page_content, {"slug": slug})
        return page_content
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

