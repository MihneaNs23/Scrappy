import time
from urllib.parse import urlparse, urlunparse

CACHE_TTL_SECONDS = 30 * 60  # 30 minutes

_page_cache: dict[str, dict] = {}


def normalize_cache_url(url: str) -> str:
    """
    Normalize a URL so small formatting differences do not create separate cache keys.
    """
    parsed = urlparse(url.strip())

    scheme = parsed.scheme or "https"
    netloc = parsed.netloc.lower()
    path = parsed.path or "/"

    if not netloc and parsed.path:
        # Handles inputs like "example.com/page"
        reparsed = urlparse(f"{scheme}://{url.strip()}")
        scheme = reparsed.scheme
        netloc = reparsed.netloc.lower()
        path = reparsed.path or "/"
        parsed = reparsed

    normalized = parsed._replace(
        scheme=scheme,
        netloc=netloc,
        path=path,
        params="",
        query=parsed.query,
        fragment="",
    )

    return urlunparse(normalized)


def clear_expired_cache() -> None:
    now = time.time()
    expired_keys = [
        key for key, value in _page_cache.items()
        if value["expires_at"] <= now
    ]

    for key in expired_keys:
        del _page_cache[key]


def get_cached_page(url: str) -> dict | None:
    clear_expired_cache()

    key = normalize_cache_url(url)
    entry = _page_cache.get(key)

    if not entry:
        return None

    return entry["data"]


def set_cached_page(url: str, data: dict) -> None:
    clear_expired_cache()

    key = normalize_cache_url(url)
    _page_cache[key] = {
        "expires_at": time.time() + CACHE_TTL_SECONDS,
        "data": data,
    }


def get_cache_stats() -> dict:
    clear_expired_cache()
    return {
        "entries": len(_page_cache),
        "ttl_seconds": CACHE_TTL_SECONDS,
    }


def clear_all_cache() -> None:
    _page_cache.clear()