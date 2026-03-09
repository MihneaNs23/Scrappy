import os
import re

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

ALLOWED_PAGE_TYPES = {
    "article",
    "product page",
    "job posting",
    "research paper",
    "documentation",
    "forum/discussion",
    "other",
}


def _normalize(value: str | None) -> str:
    return (value or "").strip().lower()


def _contains_any(text: str, terms: list[str]) -> bool:
    return any(term in text for term in terms)


def _word_count(text: str) -> int:
    return len(re.findall(r"\w+", text))


def _rule_based_classification(
    url: str,
    title: str,
    meta_description: str,
    content: str,
) -> str | None:
    url_l = _normalize(url)
    title_l = _normalize(title)
    meta_l = _normalize(meta_description)
    content_l = _normalize(content[:12000])

    combined = f"{title_l}\n{meta_l}\n{content_l}"

    forum_domains = [
        "stackoverflow.com",
        "reddit.com",
        "discuss.python.org",
        "forum.",
        "/forum/",
        "/questions/",
        "/thread/",
    ]
    if _contains_any(url_l, forum_domains):
        return "forum/discussion"

    documentation_domains = [
        "docs.python.org",
        "fastapi.tiangolo.com",
        "react.dev",
        "developer.mozilla.org",
        "readthedocs",
        "/docs/",
        "/reference/",
    ]
    if _contains_any(url_l, documentation_domains):
        return "documentation"

    research_domains = [
        "arxiv.org",
        "doi.org",
        "/abs/",
        "/paper/",
        "/publication/",
    ]
    if _contains_any(url_l, research_domains):
        return "research paper"

    job_url_hints = [
        "/jobs/",
        "/job/",
        "/careers/",
        "/career/",
        "/vacature/",
        "/vacatures/",
        "greenhouse.io",
        "lever.co",
        "ashbyhq.com",
        "indeed",
    ]
    if _contains_any(url_l, job_url_hints):
        return "job posting"

    product_url_hints = [
        "/product/",
        "/products/",
        "/p/",
        "/dp/",
        "mediamarkt.",
        "coolblue.",
        "apple.com/iphone",
        "electronics/",
        "shop.",
        "store.",
    ]
    if _contains_any(url_l, product_url_hints):
        return "product page"

    if "wikipedia.org/wiki/" in url_l:
        return "article"

    if _contains_any(
        combined,
        ["api reference", "parameters", "returns", "example usage", "source code"],
    ):
        return "documentation"

    if _contains_any(
        combined,
        ["abstract", "authors", "references", "methodology", "paper proposes"],
    ):
        return "research paper"

    if _contains_any(
        combined,
        ["apply now", "requirements", "responsibilities", "salary", "vacature", "full-time", "part-time"],
    ):
        return "job posting"

    if _contains_any(
        combined,
        ["add to cart", "buy now", "in stock", "out of stock", "specifications", "customer reviews", "prijs", "winkelwagen"],
    ):
        return "product page"

    if _contains_any(
        combined,
        ["asked", "answered", "comments", "replies", "upvote", "accepted answer"],
    ):
        return "forum/discussion"

    if _contains_any(url_l, ["/blog/", "/news/", "/article/", "/reviews/"]):
        return "article"

    if _word_count(content_l) > 200:
        return "article"

    return None


def classify_page(
    url: str,
    title: str | None,
    meta_description: str | None,
    content: str,
) -> str:
    cleaned_content = content.strip()

    if not cleaned_content:
        return "other"

    title = title or ""
    meta_description = meta_description or ""

    rule_label = _rule_based_classification(
        url=url,
        title=title,
        meta_description=meta_description,
        content=cleaned_content,
    )
    if rule_label in ALLOWED_PAGE_TYPES:
        return rule_label

    shortened_content = cleaned_content[:5000]

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You classify webpages into exactly one category. "
                    "Return only one of these labels and nothing else:\n"
                    "article\n"
                    "product page\n"
                    "job posting\n"
                    "research paper\n"
                    "documentation\n"
                    "forum/discussion\n"
                    "other\n\n"
                    "Use all available signals: URL, page title, meta description, and content."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"URL:\n{url}\n\n"
                    f"Page title:\n{title or 'N/A'}\n\n"
                    f"Meta description:\n{meta_description or 'N/A'}\n\n"
                    f"Content preview:\n{shortened_content}\n\n"
                    "Classify this page into exactly one allowed label."
                ),
            },
        ],
        max_tokens=20,
        temperature=0,
    )

    label = response.choices[0].message.content
    label = label.strip().lower() if label else "other"

    if label not in ALLOWED_PAGE_TYPES:
        return "other"

    return label