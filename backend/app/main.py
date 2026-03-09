from fastapi import FastAPI

from app.routes.analyze import router as analyze_router
from app.routes.ask import router as ask_router

app = FastAPI(
    title="Ask-This-Page API",
    description="Analyze webpages, cache their extracted content, and answer questions about them.",
    version="0.2.0",
)

app.include_router(analyze_router)
app.include_router(ask_router)


@app.get("/")
def root():
    return {"message": "Ask-This-Page API running"}