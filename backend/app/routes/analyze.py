import asyncio

from fastapi import APIRouter, HTTPException

from app.services.classify_page import classify_page
from app.services.extract_content import extract_page_data
from app.services.extract_structured_data import extract_structured_data
from app.services.fetch_page import fetch_page
from app.services.page_cache import get_cached_page, set_cached_page
from app.services.summarize_page import summarize_page

router = APIRouter()


@router.get("/analyze")
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

            return {
                "url": cached_page["url"],
                "page_type": cached_page["page_type"],
                "summary": cached_page["summary"],
                "structured_data": cached_page.get("structured_data"),
                "title": cached_page.get("title"),
                "meta_description": cached_page.get("meta_description"),
                "content_preview": content[:2000],
                "content_length": len(content),
                "cached": True,
            }

        html = await fetch_page(normalized_url)

        page_data = extract_page_data(html)
        content = page_data["content"]
        title = page_data.get("title")
        meta_description = page_data.get("meta_description")

        page_type = classify_page(
            url=normalized_url,
            title=title,
            meta_description=meta_description,
            content=content,
        )

        summary_task = asyncio.to_thread(summarize_page, content)
        structured_task = asyncio.to_thread(extract_structured_data, content, page_type)

        summary, structured_data = await asyncio.gather(summary_task, structured_task)

        cache_data = {
            "url": normalized_url,
            "content": content,
            "page_type": page_type,
            "summary": summary,
            "structured_data": (
                structured_data.model_dump()
                if structured_data and hasattr(structured_data, "model_dump")
                else structured_data
            ),
            "title": title,
            "meta_description": meta_description,
        }

        set_cached_page(normalized_url, cache_data)

        return {
            "url": normalized_url,
            "page_type": page_type,
            "summary": summary,
            "structured_data": cache_data["structured_data"],
            "title": title,
            "meta_description": meta_description,
            "content_preview": content[:2000],
            "content_length": len(content),
            "cached": False,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))