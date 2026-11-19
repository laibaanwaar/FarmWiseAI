"""Tiny, keyless retrieval engine over the bundled handbook knowledge base.

The demo stays useful without any API key: answers are composed only from
handbook entries, so every reply carries a real citation.
"""

from __future__ import annotations

import re

from farmwise.data import KNOWLEDGE

STOPWORDS = {
    "the", "a", "an", "is", "are", "do", "does", "how", "what", "when", "which", "i",
    "my", "to", "for", "of", "in", "on", "and", "can", "should", "with", "best", "it",
    "this", "that", "be", "was", "are", "me", "you", "we", "at", "by", "from", "much",
}


def _tokens(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z]+", text.lower()) if w not in STOPWORDS and len(w) > 1}


def retrieve(question: str, crop: str | None = None) -> dict | None:
    """Return the best matching handbook entry for a question, or None."""
    question = (question or "").strip()
    if not question:
        return None

    q_lower = question.lower()
    q_tokens = _tokens(question)
    best, best_score = None, 0.0

    for entry in KNOWLEDGE:
        score = 0.0
        for keyword in entry["keywords"]:
            if keyword in q_lower:
                score += 3.0
        score += len(q_tokens & _tokens(entry["title"] + " " + entry["heading"] + " " + entry["section"]))
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
            "text_en": "I could not find this in the indexed handbooks yet. Try asking about wheat urea timing, rice water management, cotton whitefly or Fusarium wilt.",
            "text_ur": "یہ سوال ابھی انڈیکس شدہ ہینڈ بکس میں موجود نہیں ملا۔ گندم میں یوریا کے وقت، چاول میں پانی، کپاس میں سفید مکھی یا فیوزیریم ولٹ کے بارے میں پوچھیں۔",
        }

    return {
        "ok": True,
        "question": question,
        "entry": entry,
        "text_en": f"According to {entry['doc']}, p. {entry['printed_page']}: {entry['snippet_en']}",
        "text_ur": f"{entry['doc']}، صفحہ {entry['printed_page']} کے مطابق: {entry['snippet_ur']}",
    }


def entry_by_id(entry_id: str) -> dict | None:
    return next((e for e in KNOWLEDGE if e["id"] == entry_id), None)
