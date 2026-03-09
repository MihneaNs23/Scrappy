import os

from openai import OpenAI
from dotenv import load_dotenv

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


def classify_page(content: str) -> str:
    cleaned_content = content.strip()

    if not cleaned_content:
        return "other"

    shortened_content = cleaned_content[:4000]

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
                    "other"
                ),
            },
            {
                "role": "user",
                "content": (
                    "Classify this webpage content into exactly one allowed label.\n\n"
                    f"{shortened_content}"
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