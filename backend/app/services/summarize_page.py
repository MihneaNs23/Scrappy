import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def summarize_page(content: str) -> str:
    """
    Generate a short summary of webpage content.
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "You summarize webpages clearly and concisely."
            },
            {
                "role": "user",
                "content": f"Summarize this webpage:\n\n{content[:4000]}"
            }
        ],
        max_tokens=200
    )

    return response.choices[0].message.content