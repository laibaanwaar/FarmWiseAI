
import os
from functools import lru_cache

from langchain_groq import ChatGroq


def detect_language(text: str) -> str:
    """Detect Urdu script or default to English."""
    urdu_characters = sum(
        1 for char in text
        if "\u0600" <= char <= "\u06FF"
    )

    return "Urdu" if urdu_characters > 0 else "English"


def is_urdu(text: str) -> bool:
    """Check whether the question is written in Urdu script."""
    return detect_language(text) == "Urdu"


@lru_cache(maxsize=1)
def get_translation_model():
    """Create and reuse Groq model for translation."""
    return ChatGroq(
        model=os.environ["GROQ_MODEL"],
        temperature=0,
    )


def translate_query_to_english(question: str) -> str:
    """Translate Urdu question into an English search query."""

    if not question.strip():
        raise ValueError("Question cannot be empty.")

    if not is_urdu(question):
        return question.strip()

    model = get_translation_model()

    response = model.invoke([
        (
            "system",
            "Translate the Urdu agricultural question into English. "
            "Preserve crop names and disease terminology. "
            "Return only the English translation. "
            "Do not answer the question."
        ),
        ("human", question),
    ])

    return response.content.strip()
