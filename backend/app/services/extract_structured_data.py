from __future__ import annotations

import json
import os
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI

from app.models.schemas import (
    ArticleData,
    DocumentationData,
    ForumDiscussionData,
    JobPostingData,
    OtherPageData,
    ProductPageData,
    ResearchPaperData,
    StructuredData,
)

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

MAX_INPUT_CHARS = 7000
MODEL_NAME = "gpt-4o-mini"


def extract_structured_data(content: str, page_type: str) -> StructuredData | None:
    cleaned_content = content.strip()

    if not cleaned_content:
        return None

    shortened_content = cleaned_content[:MAX_INPUT_CHARS]

    if page_type == "job posting":
        return _extract_job_posting(shortened_content)

    if page_type == "product page":
        return _extract_product_page(shortened_content)

    if page_type == "research paper":
        return _extract_research_paper(shortened_content)

    if page_type == "article":
        return _extract_article(shortened_content)

    if page_type == "documentation":
        return _extract_documentation(shortened_content)

    if page_type == "forum/discussion":
        return _extract_forum_discussion(shortened_content)

    return _extract_other(shortened_content)


def _call_json_extraction(system_prompt: str, user_prompt: str) -> dict[str, Any]:
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=500,
        temperature=0,
        response_format={"type": "json_object"},
    )

    raw_content = response.choices[0].message.content
    if not raw_content:
        raise Exception("Structured extraction returned an empty response.")

    return json.loads(raw_content)


def _extract_job_posting(content: str) -> JobPostingData:
    data = _call_json_extraction(
        system_prompt=(
            "You extract structured data from job posting pages. "
            "Return valid JSON only. "
            "Use null when a field is not present. "
            "Use empty arrays when list data is not present. "
            "Do not invent information."
        ),
        user_prompt=(
            "Extract the following fields from this job posting page:\n"
            "- page_type\n"
            "- title\n"
            "- company\n"
            "- location\n"
            "- salary\n"
            "- employment_type\n"
            "- requirements (array)\n"
            "- responsibilities (array)\n"
            "- application_deadline\n\n"
            "Set page_type to exactly 'job posting'.\n\n"
            f"Page content:\n{content}"
        ),
    )
    data["page_type"] = "job posting"
    return JobPostingData.model_validate(data)


def _extract_product_page(content: str) -> ProductPageData:
    data = _call_json_extraction(
        system_prompt=(
            "You extract structured data from product pages. "
            "Return valid JSON only. "
            "Use null when a field is not present. "
            "Use empty arrays or empty objects when needed. "
            "Do not invent information."
        ),
        user_prompt=(
            "Extract the following fields from this product page:\n"
            "- page_type\n"
            "- product_name\n"
            "- brand\n"
            "- price\n"
            "- currency\n"
            "- availability\n"
            "- rating\n"
            "- features (array)\n"
            "- specifications (object of key-value pairs)\n\n"
            "Set page_type to exactly 'product page'.\n\n"
            f"Page content:\n{content}"
        ),
    )
    data["page_type"] = "product page"
    return ProductPageData.model_validate(data)


def _extract_research_paper(content: str) -> ResearchPaperData:
    data = _call_json_extraction(
        system_prompt=(
            "You extract structured data from research paper pages. "
            "Return valid JSON only. "
            "Use null when a field is not present. "
            "Use empty arrays when list data is not present. "
            "Do not invent information."
        ),
        user_prompt=(
            "Extract the following fields from this research paper page:\n"
            "- page_type\n"
            "- title\n"
            "- authors (array)\n"
            "- publication\n"
            "- year\n"
            "- research_question\n"
            "- methodology\n"
            "- key_findings (array)\n\n"
            "Set page_type to exactly 'research paper'.\n\n"
            f"Page content:\n{content}"
        ),
    )
    data["page_type"] = "research paper"
    return ResearchPaperData.model_validate(data)


def _extract_article(content: str) -> ArticleData:
    data = _call_json_extraction(
        system_prompt=(
            "You extract structured data from article pages. "
            "Return valid JSON only. "
            "Use null when a field is not present. "
            "Use empty arrays when list data is not present. "
            "Do not invent information."
        ),
        user_prompt=(
            "Extract the following fields from this article page:\n"
            "- page_type\n"
            "- title\n"
            "- author\n"
            "- publish_date\n"
            "- topic\n"
            "- key_points (array)\n\n"
            "Set page_type to exactly 'article'.\n\n"
            f"Page content:\n{content}"
        ),
    )
    data["page_type"] = "article"
    return ArticleData.model_validate(data)


def _extract_documentation(content: str) -> DocumentationData:
    data = _call_json_extraction(
        system_prompt=(
            "You extract structured data from documentation pages. "
            "Return valid JSON only. "
            "Use null when a field is not present. "
            "Use empty arrays when list data is not present. "
            "Do not invent information."
        ),
        user_prompt=(
            "Extract the following fields from this documentation page:\n"
            "- page_type\n"
            "- title\n"
            "- product_or_library\n"
            "- section\n"
            "- key_concepts (array)\n"
            "- code_examples_present (boolean or null)\n\n"
            "Set page_type to exactly 'documentation'.\n\n"
            f"Page content:\n{content}"
        ),
    )
    data["page_type"] = "documentation"
    return DocumentationData.model_validate(data)


def _extract_forum_discussion(content: str) -> ForumDiscussionData:
    data = _call_json_extraction(
        system_prompt=(
            "You extract structured data from forum or discussion pages. "
            "Return valid JSON only. "
            "Use null when a field is not present. "
            "Use empty arrays when list data is not present. "
            "Do not invent information."
        ),
        user_prompt=(
            "Extract the following fields from this forum/discussion page:\n"
            "- page_type\n"
            "- title\n"
            "- main_question\n"
            "- accepted_answer\n"
            "- key_replies (array)\n\n"
            "Set page_type to exactly 'forum/discussion'.\n\n"
            f"Page content:\n{content}"
        ),
    )
    data["page_type"] = "forum/discussion"
    return ForumDiscussionData.model_validate(data)


def _extract_other(content: str) -> OtherPageData:
    data = _call_json_extraction(
        system_prompt=(
            "You extract lightweight structured data from webpages that do not fit a known category. "
            "Return valid JSON only. "
            "Use null when a field is not present. "
            "Use empty arrays when list data is not present. "
            "Do not invent information."
        ),
        user_prompt=(
            "Extract the following fields from this webpage:\n"
            "- page_type\n"
            "- title\n"
            "- key_topics (array)\n\n"
            "Set page_type to exactly 'other'.\n\n"
            f"Page content:\n{content}"
        ),
    )
    data["page_type"] = "other"
    return OtherPageData.model_validate(data)