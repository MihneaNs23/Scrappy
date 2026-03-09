import json
import os
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI

from app.services.text_utils import clean_text, select_relevant_chunks, split_into_chunks

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

MAX_CONTEXT_CHUNKS = 4
MAX_ANSWER_TOKENS = 260


def _normalize_question(question: str) -> str:
    return question.strip().lower()


def _is_broad_question(question: str) -> bool:
    q = _normalize_question(question)

    broad_patterns = [
        "what is this page about",
        "what is this article about",
        "what is the scope",
        "what does this page cover",
        "what does this article cover",
        "what is the main point",
        "what is the main idea",
        "summarize this page",
        "summarise this page",
        "give me a summary",
        "what is this about",
        "what does it discuss",
    ]

    return any(pattern in q for pattern in broad_patterns)


def _looks_like_structured_question(
    question: str, structured_data: dict[str, Any] | None
) -> bool:
    if not structured_data:
        return False

    q = _normalize_question(question)

    field_hints = [
        "salary",
        "company",
        "location",
        "requirements",
        "responsibilities",
        "deadline",
        "price",
        "brand",
        "availability",
        "rating",
        "features",
        "specifications",
        "authors",
        "publication",
        "research question",
        "methodology",
        "findings",
        "key findings",
        "key concepts",
        "author",
        "publish date",
        "topic",
        "title",
    ]

    return any(hint in q for hint in field_hints)


def _call_llm(system_prompt: str, user_prompt: str) -> str:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=MAX_ANSWER_TOKENS,
        temperature=0.2,
    )

    answer = response.choices[0].message.content
    return answer.strip() if answer else "No answer generated."


def _answer_from_summary(
    question: str,
    summary: str,
    page_type: str | None,
    structured_data: dict[str, Any] | None,
) -> str:
    return _call_llm(
        system_prompt=(
            "You answer broad questions about a webpage using the cached page summary "
            "and optional structured data. Keep answers concise and grounded."
        ),
        user_prompt=(
            f"Question:\n{question}\n\n"
            f"Page type:\n{page_type or 'unknown'}\n\n"
            f"Summary:\n{summary}\n\n"
            f"Structured data:\n{json.dumps(structured_data or {}, ensure_ascii=False, indent=2)}\n\n"
            "Answer the question using only this information."
        ),
    )


def _answer_from_structured_data(
    question: str,
    structured_data: dict[str, Any],
    page_type: str | None,
) -> str:
    return _call_llm(
        system_prompt=(
            "You answer questions using only the provided structured webpage data. "
            "If the answer is not available in the structured data, say exactly: "
            "'Not found in the structured page data.'"
        ),
        user_prompt=(
            f"Question:\n{question}\n\n"
            f"Page type:\n{page_type or 'unknown'}\n\n"
            f"Structured data:\n{json.dumps(structured_data, ensure_ascii=False, indent=2)}"
        ),
    )


def _retrieve_context_and_answer(content: str, question: str) -> str:
    cleaned_content = clean_text(content)
    chunks = split_into_chunks(cleaned_content)

    relevant_chunks = select_relevant_chunks(
        chunks=chunks,
        question=question,
        top_k=MAX_CONTEXT_CHUNKS,
    )

    context = "\n\n---\n\n".join(
        f"Relevant section {i + 1}:\n{chunk}"
        for i, chunk in enumerate(relevant_chunks)
    )

    return _call_llm(
        system_prompt=(
            "You answer questions about webpage content. "
            "Use only the provided webpage sections. "
            "If the answer is not present in the provided text, say exactly: "
            "'Not found in the page content.'"
        ),
        user_prompt=(
            f"Question:\n{question}\n\n"
            f"Relevant webpage sections:\n\n{context}"
        ),
    )


def answer_question(
    content: str,
    question: str,
    summary: str | None = None,
    page_type: str | None = None,
    structured_data: dict[str, Any] | None = None,
) -> str:
    cleaned_content = clean_text(content)
    cleaned_question = question.strip()

    if not cleaned_content:
        raise Exception("No readable page content available for question answering.")

    if not cleaned_question:
        raise Exception("Question cannot be empty.")

    if _is_broad_question(cleaned_question) and summary:
        return _answer_from_summary(
            question=cleaned_question,
            summary=summary,
            page_type=page_type,
            structured_data=structured_data,
        )

    if _looks_like_structured_question(cleaned_question, structured_data):
        structured_answer = _answer_from_structured_data(
            question=cleaned_question,
            structured_data=structured_data or {},
            page_type=page_type,
        )
        if structured_answer != "Not found in the structured page data.":
            return structured_answer

    retrieval_answer = _retrieve_context_and_answer(
        content=cleaned_content,
        question=cleaned_question,
    )

    if (
        retrieval_answer == "Not found in the page content."
        and summary
        and _is_broad_question(cleaned_question)
    ):
        return _answer_from_summary(
            question=cleaned_question,
            summary=summary,
            page_type=page_type,
            structured_data=structured_data,
        )

    return retrieval_answer