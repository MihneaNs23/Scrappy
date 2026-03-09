import os

from openai import OpenAI
from dotenv import load_dotenv

from app.services.text_utils import clean_text, split_into_chunks, select_relevant_chunks

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

MAX_CONTEXT_CHUNKS = 3
MAX_ANSWER_TOKENS = 220


def answer_question(content: str, question: str) -> str:
    cleaned_content = clean_text(content)
    cleaned_question = question.strip()

    if not cleaned_content:
        raise Exception("No readable page content available for question answering.")

    if not cleaned_question:
        raise Exception("Question cannot be empty.")

    chunks = split_into_chunks(cleaned_content)
    relevant_chunks = select_relevant_chunks(
        chunks=chunks,
        question=cleaned_question,
        top_k=MAX_CONTEXT_CHUNKS,
    )

    context = "\n\n---\n\n".join(
        f"Relevant section {i + 1}:\n{chunk}"
        for i, chunk in enumerate(relevant_chunks)
    )

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You answer questions about webpage content. "
                    "Use only the provided webpage sections. "
                    "If the answer is not present in the provided text, say exactly: "
                    "'Not found in the page content.'"
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Question:\n{cleaned_question}\n\n"
                    f"Relevant webpage sections:\n\n{context}"
                ),
            },
        ],
        max_tokens=MAX_ANSWER_TOKENS,
        temperature=0.2,
    )

    answer = response.choices[0].message.content
    return answer.strip() if answer else "No answer generated."