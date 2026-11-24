
"""Lightweight bilingual handbook retrieval engine."""

from __future__ import annotations

import re

from farmwise.data import KNOWLEDGE

STOPWORDS = {
    "the", "a", "an", "is", "are", "do", "does", "how", "what", "when",
    "which", "i", "my", "to", "for", "of", "in", "on", "and", "can",
    "should", "with", "best", "it", "this", "that", "be", "was", "me",
    "you", "we", "at", "by", "from", "much",
}

# Common Urdu agricultural words mapped to existing handbook keywords.
URDU_ALIASES = {
    "گندم": "gandum wheat",
    "یوریا": "urea yuria",
    "کھاد": "khad fertilizer",
    "نائٹروجن": "nitrogen",
    "پانی": "pani water",
    "آبپاشی": "abpashi irrigation",
    "آبپاشی": "abpashi irrigation",
    "چاول": "rice",
    "دھان": "rice",
    "کپاس": "cotton",
    "سفید مکھی": "whitefly",
    "فیوزیریم ولٹ": "fusarium wilt",
    "فوزیریم ولٹ": "fusarium wilt",
    "بیماری": "disease",
    "کیڑا": "pest",
    "کیڑے": "pest",
    "پہلی آبپاشی": "first irrigation",
    "ٹلرنگ": "tillering",
}


def _normalize_urdu(text: str) -> str:
    """Convert common Urdu agricultural terms to searchable keywords."""
    normalized = text.lower()

    # Replace longer phrases first.
    for urdu, english in sorted(
        URDU_ALIASES.items(), key=lambda item: len(item[0]), reverse=True
    ):
        normalized = normalized.replace(urdu, f" {english} ")

    return normalized


def _tokens(text: str) -> set[str]:
    normalized = _normalize_urdu(text)
    return {
        word
        for word in re.findall(r"[a-z]+", normalized)
        if word not in STOPWORDS and len(word) > 1
    }


def retrieve(question: str, crop: str | None = None) -> dict | None:
    """Return the best matching handbook entry for a question, or None."""
    question = (question or "").strip()
    if not question:
        return None

    q_normalized = _normalize_urdu(question)
    q_tokens = _tokens(question)

    best, best_score = None, 0.0

    for entry in KNOWLEDGE:
        score = 0.0

        for keyword in entry["keywords"]:
            if keyword.lower() in q_normalized:
                score += 3.0

        searchable_text = (
            entry["title"] + " " + entry["heading"] + " " + entry["section"]
        )

        score += len(q_tokens & _tokens(searchable_text))
        score += 0.6 * len(q_tokens & _tokens(entry["snippet_en"]))

        if crop:
            score += 2.5 if entry["crop"] == crop else -1.5

        if score > best_score:
            best, best_score = entry, score

    return best if best_score >= 3.0 else None


def answer(question: str, crop: str | None = None) -> dict:
    """Answer envelope used by the chat UI."""
    entry = retrieve(question, crop)

    if entry is None:
        return {
            "ok": False,
            "question": question,
            "text_en": (
                "I could not find this in the indexed handbooks yet. "
                "Try asking about wheat urea timing, rice water management, "
                "cotton whitefly or Fusarium wilt."
            ),
            "text_ur": (
                "یہ سوال ابھی انڈیکس شدہ ہینڈ بکس میں موجود نہیں ملا۔ "
                "گندم میں یوریا کے وقت، چاول میں پانی، کپاس میں سفید مکھی "
                "یا فیوزیریم ولٹ کے بارے میں پوچھیں۔"
            ),
        }

    return {
        "ok": True,
        "question": question,
        "entry": entry,
        "text_en": (
            f"According to {entry['doc']}, p. "
            f"{entry['printed_page']}: {entry['snippet_en']}"
        ),
        "text_ur": (
            f"{entry['doc']}، صفحہ {entry['printed_page']} کے مطابق: "
            f"{entry['snippet_ur']}"
        ),
    }


def entry_by_id(entry_id: str) -> dict | None:
    return next((entry for entry in KNOWLEDGE if entry["id"] == entry_id), None)
