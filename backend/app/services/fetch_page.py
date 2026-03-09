import httpx
import certifi

async def fetch_page(url: str) -> str:
    """
    Download the HTML of a webpage.
    """
    try:
        async with httpx.AsyncClient(
            timeout=20,
            follow_redirects=True,
            verify=certifi.where()
        ) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.text

    except httpx.RequestError as e:
        raise Exception(f"Request failed: {str(e)}")

    except httpx.HTTPStatusError as e:
        raise Exception(f"HTTP error: {e.response.status_code} for URL: {url}")