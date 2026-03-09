from fastapi import APIRouter, HTTPException

from app.models.schemas import AnalyzeResponse, CacheEntry
from app.services.classify_page import classify_page
from app.services.extract_content import extract_content
from app.services.extract_structured_data import extract_structured_data
from app.services.fetch_page import fetch_page
from app.services.page_cache import get_cached_page, set_cached_page
from app.services.summarize_page import summarize_page

router = APIRouter()


@router.get("/analyze", response_model=AnalyzeResponse)
async def analyze_page(url: str):
    try:
        normalized_url = url.strip()
        if not normalized_url:
            raise HTTPException(status_code=400, detail="URL is required.")

        cached_page = get_cached_page(normalized_url)

        if (
            cached_page
            and cached_page.get("content")
            and cached_page.get("page_type")
            and cached_page.get("summary")
        ):
            content = cached_page["content"]

            return AnalyzeResponse(
                url=cached_page["url"],
                page_type=cached_page["page_type"],
                summary=cached_page["summary"],
                structured_data=cached_page.get("structured_data"),
                content_preview=content[:2000],
                content_length=len(content),
                cached=True,
            )

        html = await fetch_page(normalized_url)
        content = extract_content(html)
        page_type = classify_page(content)
        summary = summarize_page(content)
        structured_data = extract_structured_data(content, page_type)

        cache_entry = CacheEntry(
            url=normalized_url,
            content=content,
            page_type=page_type,
            summary=summary,
            structured_data=structured_data.model_dump() if structured_data else None,
        )

        set_cached_page(normalized_url, cache_entry.model_dump())

        return AnalyzeResponse(
            url=normalized_url,
            page_type=page_type,
            summary=summary,
            structured_data=structured_data,
            content_preview=content[:2000],
            content_length=len(content),
            cached=False,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))