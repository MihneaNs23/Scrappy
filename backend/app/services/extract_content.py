import trafilatura
from bs4 import BeautifulSoup


def extract_with_trafilatura(html: str) -> str | None:
    """Primary content extraction."""
    try:
        text = trafilatura.extract(
            html,
            include_comments=False,
            include_tables=False,
        )

        if text and len(text) > 300:
            return text

    except Exception:
        pass

    return None


def extract_with_bs4(html: str) -> str | None:
    """Fallback extraction using BeautifulSoup."""
    soup = BeautifulSoup(html, "html.parser")

    # Remove non-content elements
    for tag in soup(["script", "style", "noscript", "header", "footer", "nav"]):
        tag.decompose()

    candidates = []

    # Try common article containers
    selectors = [
        "article",
        "main",
        "[role=main]",
        ".content",
        ".post",
        ".article",
    ]

    for selector in selectors:
        elements = soup.select(selector)

        for el in elements:
            text = el.get_text(separator=" ", strip=True)

            if len(text) > 500:
                candidates.append(text)

    if candidates:
        return max(candidates, key=len)

    # fallback to body
    body = soup.body

    if body:
        text = body.get_text(separator=" ", strip=True)

        if len(text) > 500:
            return text

    return None


def extract_content(html: str) -> str:
    """
    Extract readable text from HTML.

    Strategy:
    1. Trafilatura (best for articles/docs)
    2. BeautifulSoup fallback
    """

    text = extract_with_trafilatura(html)

    if text:
        return text

    text = extract_with_bs4(html)

    if text:
        return text

    raise ValueError("Could not extract readable content")