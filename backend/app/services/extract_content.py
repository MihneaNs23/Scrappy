import trafilatura


def extract_content(html: str) -> str:
    """
    Extract the main readable content from raw HTML.
    """
    extracted_text = trafilatura.extract(html)

    if not extracted_text:
        raise Exception("Could not extract readable content from page.")

    return extracted_text