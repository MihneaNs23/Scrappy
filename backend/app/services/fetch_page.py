import asyncio
from urllib.parse import urlparse

import httpx

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,"
        "image/avif,image/webp,image/apng,*/*;q=0.8"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
}


def normalize_url(url: str) -> str:
    parsed = urlparse(url)
    if not parsed.scheme:
        return "https://" + url
    return url


def looks_like_blocked_page(html: str) -> bool:
    lower = html.lower()

    indicators = [
        "enable javascript",
        "please enable javascript",
        "access denied",
        "forbidden",
        "captcha",
        "verify you are human",
        "bot detection",
        "cloudflare",
    ]

    return any(indicator in lower for indicator in indicators)


async def fetch_with_httpx(url: str) -> str:
    async with httpx.AsyncClient(
        headers=DEFAULT_HEADERS,
        timeout=20,
        follow_redirects=True,
    ) as client:
        response = await client.get(url)

        if response.status_code >= 400:
            raise ValueError(f"Blocked with status {response.status_code}")

        content_type = response.headers.get("content-type", "").lower()
        if "text/html" not in content_type:
            raise ValueError(f"URL did not return HTML (content-type: {content_type})")

        html = response.text

        if len(html) < 1000 or looks_like_blocked_page(html):
            raise ValueError("Page likely blocked or JS-rendered")

        return html


def fetch_with_playwright_sync(url: str) -> str:
    from playwright.sync_api import sync_playwright

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)

            context = browser.new_context(
                user_agent=DEFAULT_HEADERS["User-Agent"],
                locale="en-US",
                extra_http_headers={
                    "Accept-Language": DEFAULT_HEADERS["Accept-Language"],
                    "Cache-Control": DEFAULT_HEADERS["Cache-Control"],
                    "Pragma": DEFAULT_HEADERS["Pragma"],
                },
                viewport={"width": 1440, "height": 900},
            )

            page = context.new_page()
            page.goto(url, wait_until="domcontentloaded", timeout=15000)
            page.wait_for_timeout(1000)

            html = page.content()

            context.close()
            browser.close()

            if len(html) < 500:
                raise ValueError("Playwright returned very small page")

            return html

    except Exception as e:
        raise RuntimeError(f"Playwright failed: {e}")


async def fetch_with_playwright(url: str) -> str:
    return await asyncio.to_thread(fetch_with_playwright_sync, url)


async def fetch_page(url: str) -> str:
    url = normalize_url(url)

    try:
        return await fetch_with_httpx(url)
    except Exception as httpx_error:
        try:
            return await fetch_with_playwright(url)
        except Exception as playwright_error:
            raise RuntimeError(
                "Failed to fetch page.\n"
                f"httpx error: {httpx_error}\n"
                f"playwright error: {playwright_error}"
            )