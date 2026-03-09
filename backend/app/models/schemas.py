from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, HttpUrl


class AnalyzeRequest(BaseModel):
    url: str = Field(..., min_length=1)


class AskRequest(BaseModel):
    url: str = Field(..., min_length=1)
    question: str = Field(..., min_length=1)


class AskResponse(BaseModel):
    url: str
    question: str
    answer: str
    cached: bool
    content_length: int


class BaseStructuredData(BaseModel):
    page_type: str


class JobPostingData(BaseStructuredData):
    page_type: Literal["job posting"] = "job posting"
    title: str | None = None
    company: str | None = None
    location: str | None = None
    salary: str | None = None
    employment_type: str | None = None
    requirements: list[str] = Field(default_factory=list)
    responsibilities: list[str] = Field(default_factory=list)
    application_deadline: str | None = None


class ProductPageData(BaseStructuredData):
    page_type: Literal["product page"] = "product page"
    product_name: str | None = None
    brand: str | None = None
    price: str | None = None
    currency: str | None = None
    availability: str | None = None
    rating: str | None = None
    features: list[str] = Field(default_factory=list)
    specifications: dict[str, str] = Field(default_factory=dict)


class ResearchPaperData(BaseStructuredData):
    page_type: Literal["research paper"] = "research paper"
    title: str | None = None
    authors: list[str] = Field(default_factory=list)
    publication: str | None = None
    year: str | None = None
    research_question: str | None = None
    methodology: str | None = None
    key_findings: list[str] = Field(default_factory=list)


class ArticleData(BaseStructuredData):
    page_type: Literal["article"] = "article"
    title: str | None = None
    author: str | None = None
    publish_date: str | None = None
    topic: str | None = None
    key_points: list[str] = Field(default_factory=list)


class DocumentationData(BaseStructuredData):
    page_type: Literal["documentation"] = "documentation"
    title: str | None = None
    product_or_library: str | None = None
    section: str | None = None
    key_concepts: list[str] = Field(default_factory=list)
    code_examples_present: bool | None = None


class ForumDiscussionData(BaseStructuredData):
    page_type: Literal["forum/discussion"] = "forum/discussion"
    title: str | None = None
    main_question: str | None = None
    accepted_answer: str | None = None
    key_replies: list[str] = Field(default_factory=list)


class OtherPageData(BaseStructuredData):
    page_type: Literal["other"] = "other"
    title: str | None = None
    key_topics: list[str] = Field(default_factory=list)


StructuredData = (
    JobPostingData
    | ProductPageData
    | ResearchPaperData
    | ArticleData
    | DocumentationData
    | ForumDiscussionData
    | OtherPageData
)


class AnalyzeResponse(BaseModel):
    url: str
    page_type: str
    summary: str
    structured_data: StructuredData | None = None
    content_preview: str
    content_length: int
    cached: bool


class CacheEntry(BaseModel):
    url: str
    content: str
    page_type: str
    summary: str
    structured_data: dict[str, Any] | None = None