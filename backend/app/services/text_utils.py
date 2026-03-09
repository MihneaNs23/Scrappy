import re
from typing import List


CHUNK_SIZE = 1200
CHUNK_OVERLAP = 150


def clean_text(text: str) -> str:
    if not text:
        return ""

    lines = [line.strip() for line in text.splitlines()]
    lines = [line for line in lines if line]
    cleaned = "\n".join(lines)
    cleaned = re.sub(r"\n{2,}", "\n\n", cleaned)
    return cleaned.strip()


def split_into_chunks(
    text: str,
    chunk_size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP,
) -> List[str]:
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


def _tokenize_for_matching(text: str) -> List[str]:
    return re.findall(r"\b[a-zA-Z0-9€$£]+\b", text.lower())


def select_relevant_chunks(
    chunks: List[str],
    question: str,
    top_k: int = 3,
) -> List[str]:
    if not chunks:
        return []

    question_terms = set(_tokenize_for_matching(question))

    # fallback: if question is too short or weird, just use first chunks
    if not question_terms:
        return chunks[:top_k]

    scored_chunks = []

    for index, chunk in enumerate(chunks):
        chunk_terms = _tokenize_for_matching(chunk)
        chunk_term_set = set(chunk_terms)

        overlap_score = len(question_terms.intersection(chunk_term_set))

        # small boost if full question words appear more than once
        frequency_score = sum(chunk_terms.count(term) for term in question_terms)

        score = (overlap_score * 2) + frequency_score

        scored_chunks.append((score, index, chunk))

    scored_chunks.sort(key=lambda item: (item[0], -item[1]), reverse=True)

    best = [chunk for score, _, chunk in scored_chunks[:top_k] if score > 0]

    if best:
        return best

    # if no lexical match at all, fall back to first chunks
    return chunks[:top_k]