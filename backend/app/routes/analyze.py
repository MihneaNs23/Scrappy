from fastapi import APIRouter, HTTPException
from app.services.fetch_page import fetch_page
from app.services.extract_content import extract_content
from app.services.summarize_page import summarize_page

router = APIRouter()

@router.get("/analyze")
async def analyze(url: str):
    try:
        print("Step 1: fetching page")
        html = await fetch_page(url)

        print("Step 2: extracting content")
        content = extract_content(html)
        summary = summarize_page(content)
        print("Step 3: returning response")
        return {
            "url": url,
            "html_length": len(html),
            "content": content,
            "summary": summary
        }

    except Exception as e:
        print("ERROR:", str(e))
        raise HTTPException(status_code=500, detail=str(e))