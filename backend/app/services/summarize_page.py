import os
from typing import List

from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Character-based limits for now.
# Later we can switch to token-aware chunking if needed.
CHUNK_SIZE = 3500
CHUNK_OVERLAP = 300
FINAL_SUMMARY_MAX_TOKENS = 250
CHUNK_SUMMARY_MAX_TOKENS = 180
MIN_CONTENT_LENGTH = 80


def _clean_content(content: str) -> str:
    """
    Normalize extracted text before sending it to the model.
    """
    if not content:
        return ""

    # Remove excessive blank space while preserving readability.
    lines = [line.strip() for line in content.splitlines()]
    non_empty_lines = [line for line in lines if line]
    return "\n".join(non_empty_lines).strip()


def _split_into_chunks(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    """
    Split long text into overlapping chunks.

    Overlap helps preserve context across chunk boundaries.
    """
    if not text:
        return []

    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = min(start + chunk_size, text_length)
        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end >= text_length:
            break

        start = end - overlap

    return chunks


def _call_openai_summary(system_prompt: str, user_prompt: str, max_tokens: int) -> str:
    """
    Shared helper for summary calls.
    """
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=max_tokens,
        temperature=0.2,
    )

    content = response.choices[0].message.content
    return content.strip() if content else "No summary generated."


def _summarize_single_chunk(chunk: str) -> str:
    """
    Summarize one chunk of page content.
    """
    return _call_openai_summary(
        system_prompt=(
            "You summarize webpage content clearly and concisely. "
            "Focus only on information present in the provided text."
        ),
        user_prompt=(
            "Summarize this section of a webpage.\n\n"
            "Return a concise paragraph or a few short bullet points.\n\n"
            f"{chunk}"
        ),
        max_tokens=CHUNK_SUMMARY_MAX_TOKENS,
    )


def _combine_chunk_summaries(chunk_summaries: List[str]) -> str:
    """
    Merge per-chunk summaries into one final cohesive summary.
    """
    combined_input = "\n\n".join(
        f"Section {i + 1} summary:\n{summary}"
        for i, summary in enumerate(chunk_summaries)
    )

    return _call_openai_summary(
        system_prompt=(
            "You create a final cohesive webpage summary from partial summaries. "
            "Do not invent facts. Keep the result readable, concise, and useful."
        ),
        user_prompt=(
            "Below are summaries of different sections of the same webpage.\n"
            "Create one clean final summary of the full page.\n\n"
            f"{combined_input}"
        ),
        max_tokens=FINAL_SUMMARY_MAX_TOKENS,
    )


def summarize_page(content: str) -> str:
    """
    Generate a summary of webpage content.

    Strategy:
    - Clean extracted text
    - If short: summarize directly
    - If long: split into chunks, summarize each chunk, then combine
    """
    cleaned_content = _clean_content(content)

    if not cleaned_content or len(cleaned_content) < MIN_CONTENT_LENGTH:
        raise Exception("Not enough readable content to summarize.")

    # Fast path for short pages
    if len(cleaned_content) <= CHUNK_SIZE:
        return _call_openai_summary(
            system_prompt=(
                "You summarize webpages clearly and concisely. "
                "Use only the provided content."
            ),
            user_prompt=f"Summarize this webpage:\n\n{cleaned_content}",
            max_tokens=FINAL_SUMMARY_MAX_TOKENS,
        )

    # Long-page path
    chunks = _split_into_chunks(cleaned_content)

    chunk_summaries = []
    for chunk in chunks:
        chunk_summary = _summarize_single_chunk(chunk)
        chunk_summaries.append(chunk_summary)

    return _combine_chunk_summaries(chunk_summaries)