"""Curated, exact-match Urdu demo answers backed by the local handbook."""

from __future__ import annotations

import os
import re
import unicodedata
from typing import Any

DEMO_LABEL = "پہلے سے تیار کردہ ڈیمو جواب"
INSUFFICIENT_CONTEXT_URDU = "دستیاب کتابی حوالے میں اس سوال کا مکمل جواب موجود نہیں۔"
DOCUMENT_TITLE = "Farmer’s Handbook on Basic Agriculture"


def normalize_question(question: str) -> str:
    """Normalize typography and marks for exact lookup, without fuzzy matching."""
    text = unicodedata.normalize("NFKC", question)
    text = "".join(
        char for char in text
        if unicodedata.category(char) not in {"Mn", "Mc", "Me"} and char != "ـ"
    )
    text = re.sub(r"\s+", " ", text).strip()
    text = text.rstrip(" \t\r\n؟?۔.!…")
    return re.sub(r"\s+", " ", text).strip()


def _citation(pdf_page: int, printed_page: int) -> dict[str, Any]:
    return {
        "document_title": DOCUMENT_TITLE,
        "pdf_page": pdf_page,
        "printed_page": printed_page,
    }


_ANSWER_ROWS = {
    "کپاس میں فیوزیریم وِلٹ کی کیا علامات ہیں؟": {
        "answer": (
            "کپاس میں فیوزیریم وِلٹ سے پودے کی بڑھوتری رک سکتی ہے۔ پتے پہلے کناروں سے "
            "پیلا ہونا شروع ہوتے ہیں، پھر اندر کی طرف زردی پھیلتی اور پتے جھڑ سکتے ہیں۔ "
            "تنے کے کٹے حصے میں بھورا رنگ دکھائی دے سکتا ہے؛ متاثرہ پودے جلد پھل دیتے ہیں "
            "مگر ٹینڈے چھوٹے رہتے ہیں۔ کتابچہ فصلوں کی گردش، نمٹوڈ کی آبادی کم کرنے اور "
            "مزاحم اقسام کا ذکر کرتا ہے۔"
        ),
        "citations": [_citation(89, 81)],
    },
    "کپاس کے پتے پیلے ہونے کی کیا وجوہات ہیں؟": {
        "answer": (
            "کتابچے میں کپاس کے پتوں کے پیلے ہونے کو فیوزیریم وِلٹ اور ورٹیسیلیم وِلٹ "
            "کی علامات میں شامل کیا گیا ہے۔ فیوزیریم میں زردی عموماً پتوں کے کناروں سے "
            "اندر بڑھتی ہے؛ ورٹیسیلیم میں یہ کناروں اور بڑی رگوں کے درمیان دکھائی دے سکتی "
            "ہے۔ یہ فہرست تمام ممکنہ وجوہات نہیں، اس لیے صرف زردی سے بیماری کی حتمی تشخیص "
            "نہیں کی جا سکتی۔"
        ),
        "citations": [_citation(89, 81), _citation(90, 82)],
    },
    "کپاس میں سفید مکھی کو کیسے کنٹرول کیا جا سکتا ہے؟": {
        "answer": (
            "کتابچہ کپاس میں سفید مکھی کے لیے معاشی حدِ نقصان 5–10 بالغ مکھیاں فی پتا یا "
            "20 نِمف فی پتا بتاتا ہے۔ فصل کی باقاعدہ نگرانی کریں؛ پیلے چپکنے والے پھندے "
            "چھوٹے رس چوسنے والے کیڑوں کے لیے بیان کیے گئے ہیں۔ کتابچے کے مطابق دوا آخری "
            "حل ہونی چاہیے؛ درست دوا اور مقدار مقامی زرعی توسیعی اہلکار سے معلوم کریں۔"
        ),
        "citations": [_citation(82, 74)],
    },
    "کپاس کی گلابی سنڈی سے بچاؤ کیسے کیا جائے؟": {
        "answer": (
            "دستیاب کتابچہ گلابی سنڈی کے لیے الگ ہدایات نہیں دیتا۔ اس میں عمومی طور پر کپاس "
            "کی سنڈیوں کی نگرانی اور کنٹرول کے لیے فیرومون پھندوں کا ذکر ہے، مگر یہ حوالہ "
            "گلابی سنڈی کے مخصوص طریقۂ بچاؤ یا وقت کی تصدیق نہیں کرتا۔"
        ),
        "citations": [_citation(82, 74)],
    },
    "کپاس کی کاشت کے لیے کون سی مٹی موزوں ہے؟": {
        "answer": (
            "دستیاب کتابچہ کپاس کے لیے کسی مخصوص مٹی کی قسم تجویز نہیں کرتا۔ وہ فصل کے "
            "انتخاب میں مقامی مٹی کی قسم، پی ایچ اور زرخیزی کو مدِنظر رکھنے کی ہدایت دیتا ہے۔ "
            "یہی معلومات اپنے کھیت کے لیے دیکھیں۔"
        ),
        "citations": [_citation(11, 3)],
    },
    "کپاس کو پانی کب اور کتنی بار دینا چاہیے؟": {
        "answer": (
            "کتابچے میں کپاس کے لیے آبپاشی کے اہم مراحل پھول آنے اور ٹینڈے بننے کے وقت "
            "بتائے گئے ہیں۔ اس میں پانی کی مقررہ مقدار یا آبپاشی کا وقفہ درج نہیں، اس لیے "
            "یہاں سے ایک عمومی شیڈول کی تصدیق نہیں کی جا سکتی۔"
        ),
        "citations": [_citation(25, 17)],
    },
    "کپاس میں کھاد کب اور کتنی مقدار میں ڈالنی چاہیے؟": {
        "answer": (
            "کتابچہ کھاد کی ایک مقررہ مقدار یا کپاس کے لیے مکمل وقت نامہ نہیں دیتا۔ وہ "
            "مٹی کے تجزیے کی بنیاد پر متوازن کھاد ڈالنے کی ہدایت کرتا ہے۔ درست مقدار اور "
            "وقت کے لیے دستیاب کتابی متن کافی معلومات نہیں دیتا۔"
        ),
        "citations": [_citation(95, 87)],
    },
    "کپاس کے پھول اور ٹینڈے گرنے کی کیا وجوہات ہیں؟": {
        "answer": (
            "کتابچہ پھول گرنے کی وجوہات نہیں بتاتا۔ وہ ایک وجہ کے طور پر بال روٹ کا ذکر "
            "کرتا ہے: متاثرہ ٹینڈے پہلے پانی میں بھیگے دھبوں والے ہو سکتے ہیں، پھر سیاہ "
            "یا پھپھوندی سے ڈھک سکتے ہیں، اور شدید متاثرہ ٹینڈے گر سکتے ہیں۔ ہر ٹینڈے کے "
            "گرنے کی وجہ یہی ہو، یہ کتابچہ نہیں کہتا۔"
        ),
        "citations": [_citation(89, 81)],
    },
}

_ANSWERS = {
    normalize_question(question): {
        "answer": answer["answer"],
        "citations": [dict(citation) for citation in answer["citations"]],
    }
    for question, answer in _ANSWER_ROWS.items()
}


def lookup_urdu_demo_answer(question: str) -> dict[str, Any] | None:
    """Return a copied answer only for one of the eight normalized exact matches."""
    matched = _ANSWERS.get(normalize_question(question))
    if matched is None:
        return None
    return {
        "answer": matched["answer"],
        "citations": [dict(citation) for citation in matched["citations"]],
    }


def strip_demo_label(answer: str) -> str:
    """Hide the old visible marker from demo replies already stored in history."""
    prefix = f"{DEMO_LABEL}\n\n"
    if answer.startswith(prefix):
        return answer[len(prefix):]
    if answer.startswith(DEMO_LABEL):
        return answer[len(DEMO_LABEL):].lstrip("\r\n ")
    return answer


def urdu_demo_answers_enabled() -> bool:
    return os.getenv("URDU_DEMO_ANSWERS_ENABLED", "false").strip().casefold() in {
        "1", "true", "yes", "on",
    }
