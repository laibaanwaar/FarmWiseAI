"""Groq-powered bilingual fallback for questions not answered by the handbook."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_groq import ChatGroq


PROJECT_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(PROJECT_ROOT / ".env", override=False)


def generate_bilingual_answers(question: str, crop: str) -> dict:
    """Generate English guidance and its faithful Pakistani Urdu translation."""
    api_key = os.getenv("GROQ_API_KEY")
    model_name = os.getenv("GROQ_MODEL")

    if not api_key or not model_name:
        raise RuntimeError("Groq API configuration is missing.")

    model = ChatGroq(
        model=model_name,
        temperature=0.1,
        api_key=api_key,
    )

    prompt = f"""
You are a careful agricultural guidance assistant for farmers in Pakistan.

Crop: {crop}
Farmer's question: {question}

Prepare an answer in TWO sections:

ENGLISH:
Write clear, practical guidance in simple English.

URDU:
Translate the complete English answer faithfully into natural Pakistani
Urdu script. Keep the same facts, recommendations, warnings and meaning.
Use correct agricultural terminology. Do not use Hindi or Devanagari.

IMPORTANT RULES:
- This is general AI-generated guidance, not a verified handbook answer
  or live web research.
- Never invent symptoms, facts, scientific findings or recommendations.
- Do not provide exact fertilizer or pesticide doses unless they are
  reliably established for the specific crop and situation.
- Do not recommend a chemical treatment without adequate context.
- If symptoms can have multiple causes, explain that diagnosis needs
  confirmation.
- Ask for missing details when they materially affect the advice.
- Include relevant safety precautions.
- Keep both sections concise and consistent.
- Do not claim that you consulted a handbook or verified an external source.
"""

    import re

    response = model.invoke(prompt).content

    if not isinstance(response, str) or not response.strip():
        raise ValueError("Groq returned an empty response.")

    text = response.strip()

    match = re.search(r"(?im)^\s*\**\s*ENGLISH\s*\**\s*:?\s*$", text)
    urdu_match = re.search(r"(?im)^\s*\**\s*URDU\s*\**\s*:?\s*$", text)

    if not match or not urdu_match or urdu_match.start() <= match.end():
        raise ValueError("Groq response is missing a language section.")

    english = text[match.end():urdu_match.start()].strip()
    urdu = text[urdu_match.end():].strip()

    if not english or not urdu:
        raise ValueError("Groq returned an incomplete bilingual answer.")

    return {
        "en": english,
        "ur": urdu,
    }

