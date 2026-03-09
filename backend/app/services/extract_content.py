import json
from typing import Any

import trafilatura
from bs4 import BeautifulSoup

MIN_EXTRACTED_LENGTH = 250


def _clean_join(parts: list[str]) -> str:
    seen: set[str] = set()
    cleaned_parts: list[str] = []

    for part in parts:
        normalized = " ".join((part or "").split()).strip()
        if not normalized:
            continue
        if normalized in seen:
            continue
        seen.add(normalized)
        cleaned_parts.append(normalized)

    return "\n\n".join(cleaned_parts).strip()


def _extract_title(soup: BeautifulSoup) -> str | None:
    candidates = [
        soup.find("meta", property="og:title"),
        soup.find("meta", attrs={"name": "twitter:title"}),
    ]

    for tag in candidates:
        if tag and tag.get("content"):
            title = tag.get("content", "").strip()
            if title:
                return title

    if soup.title and soup.title.string:
        title = soup.title.string.strip()
        if title:
            return title

    h1 = soup.find("h1")
    if h1:
        title = h1.get_text(" ", strip=True)
        if title:
            return title

    return None


def _extract_meta_description(soup: BeautifulSoup) -> str | None:
    candidates = [
        soup.find("meta", attrs={"name": "description"}),
        soup.find("meta", property="og:description"),
        soup.find("meta", attrs={"name": "twitter:description"}),
    ]

    for tag in candidates:
        if tag and tag.get("content"):
            description = tag.get("content", "").strip()
            if description:
                return description

    return None


def _extract_json_ld_hints(soup: BeautifulSoup) -> dict[str, Any]:
    hints: dict[str, Any] = {}

    scripts = soup.find_all("script", attrs={"type": "application/ld+json"})
    for script in scripts:
        raw = script.string or script.get_text()
        if not raw:
            continue

        try:
            data = json.loads(raw)
        except Exception:
            continue

        items = data if isinstance(data, list) else [data]

        for item in items:
            if not isinstance(item, dict):
                continue

            item_type = str(item.get("@type", "")).lower()

            if item_type and "schema_type" not in hints:
                hints["schema_type"] = item_type

            if "name" in item and "schema_name" not in hints:
                value = str(item.get("name", "")).strip()
                if value:
                    hints["schema_name"] = value

            if "description" in item and "schema_description" not in hints:
                value = str(item.get("description", "")).strip()
                if value:
                    hints["schema_description"] = value

    return hints


def extract_with_trafilatura(html: str) -> str | None:
    try:
        text = trafilatura.extract(
            html,
            include_comments=False,
            include_tables=True,
            include_links=False,
            favor_precision=False,
            favor_recall=True,
        )

        if text and len(text.strip()) >= MIN_EXTRACTED_LENGTH:
            return text.strip()

    except Exception:
        pass

    return None


def _score_candidate_text(text: str) -> int:
    normalized = " ".join(text.split())
    if not normalized:
        return 0

    length_score = min(len(normalized), 6000)
    punctuation_bonus = normalized.count(".") * 5
    heading_bonus = 100 if len(normalized.split()) > 80 else 0

    return length_score + punctuation_bonus + heading_bonus


def extract_with_bs4(html: str) -> str | None:
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup(
        [
            "script",
            "style",
            "noscript",
            "svg",
            "canvas",
            "iframe",
            "header",
            "footer",
            "nav",
            "aside",
            "form",
        ]
    ):
        tag.decompose()

    selectors = [
        ".product-detail",
        ".product-info",
        ".product-page",
        ".pdp",
        ".product",
        ".job-posting",
        ".job-description",
        ".vacancy",
        ".vacature",
        "article",
        "main",
        "[role=main]",
        ".content",
        ".main-content",
        ".article",
        ".post",
        ".entry-content",
        ".description",
        ".thread",
        ".question",
        ".answer",
        ".review",
        ".review-body",
    ]

    candidates: list[str] = []

    for selector in selectors:
        for element in soup.select(selector):
            text = element.get_text(separator=" ", strip=True)
            if len(text) >= MIN_EXTRACTED_LENGTH:
                candidates.append(text)

    if candidates:
        candidates.sort(key=_score_candidate_text, reverse=True)
        return candidates[0].strip()

    body = soup.body
    if body:
        body_text = body.get_text(separator=" ", strip=True)
        if len(body_text) >= MIN_EXTRACTED_LENGTH:
            return body_text.strip()

    return None


def extract_page_data(html: str) -> dict[str, Any]:
    soup = BeautifulSoup(html, "html.parser")

    title = _extract_title(soup)
    meta_description = _extract_meta_description(soup)
    json_ld_hints = _extract_json_ld_hints(soup)

    extracted_text = extract_with_trafilatura(html)
    if not extracted_text:
        extracted_text = extract_with_bs4(html)

    if not extracted_text:
        raise ValueError("Could not extract readable content")

    content = _clean_join(
        [
            title or "",
            meta_description or "",
            json_ld_hints.get("schema_name", "") or "",
            json_ld_hints.get("schema_description", "") or "",
            extracted_text,
        ]
    )

    if len(content) < MIN_EXTRACTED_LENGTH:
        raise ValueError("Could not extract enough readable content")

    return {
        "title": title,
        "meta_description": meta_description,
        "content": content,
        "json_ld_hints": json_ld_hints,
    }


def extract_content(html: str) -> str:
    return extract_page_data(html)["content"]