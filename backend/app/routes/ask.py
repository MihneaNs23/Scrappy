from fastapi import APIRouter, HTTPException

from app.models.schemas import AskRequest, AskResponse
from app.services.answer_question import answer_question
from app.services.page_cache import get_cached_page

router = APIRouter()


@router.post("/ask", response_model=AskResponse)
async def ask_page(request: AskRequest):
    try:
        normalized_url = request.url.strip()
        question = request.question.strip()

        if not normalized_url:
            raise HTTPException(status_code=400, detail="URL is required.")

        if not question:
            raise HTTPException(status_code=400, detail="Question is required.")

        cached_page = get_cached_page(normalized_url)

        if not cached_page or not cached_page.get("content"):
            raise HTTPException(
                status_code=400,
                detail="Page not analyzed yet. Please call /analyze first.",
            )

        content = cached_page["content"]
        answer = answer_question(content, question)

        return AskResponse(
            url=normalized_url,
            question=question,
            answer=answer,
            cached=True,
            content_length=len(content),
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))