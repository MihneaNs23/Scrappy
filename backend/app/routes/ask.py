from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.answer_question import answer_question
from app.services.page_cache import get_cached_page

router = APIRouter()


class AskRequest(BaseModel):
    url: str
    question: str


@router.post("/ask")
async def ask_page(request: AskRequest):
    try:
        normalized_url = request.url.strip()
        cleaned_question = request.question.strip()

        if not normalized_url:
            raise HTTPException(status_code=400, detail="URL is required.")

        if not cleaned_question:
            raise HTTPException(status_code=400, detail="Question is required.")

        cached_page = get_cached_page(normalized_url)

        if not cached_page or not cached_page.get("content"):
            raise HTTPException(
                status_code=400,
                detail="Page not analyzed yet. Please call /analyze first.",
            )

        content = cached_page["content"]
        summary = cached_page.get("summary")
        page_type = cached_page.get("page_type")
        structured_data = cached_page.get("structured_data")

        answer = answer_question(
            content=content,
            question=cleaned_question,
            summary=summary,
            page_type=page_type,
            structured_data=structured_data,
        )

        return {
            "url": normalized_url,
            "question": cleaned_question,
            "answer": answer,
            "cached": True,
            "content_length": len(content),
            "page_type": page_type,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))