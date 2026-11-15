import json
from pathlib import Path

from dotenv import load_dotenv

from rag.generator import generate_answer
from rag.retriever import retrieve_chunks


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def answer_question(question: str, crop: str) -> dict:
    """Retrieve a handbook passage and return an answer with its citation."""
    matches = retrieve_chunks(question, crop=crop, top_k=1)

    if not matches:
        return {
            "status": "no_passage",
            "answer": "No handbook passage was found for the selected crop.",
            "citations": [],
        }

    load_dotenv(PROJECT_ROOT / ".env")

    best_match = matches[0]
    answer = generate_answer(question, best_match["text"])
    source = best_match["metadata"]

    return {
        "status": "ok",
        "answer": answer,
        "citations": [
            {
                "document_title": source["document_title"],
                "pdf_page": source["pdf_page"],
                "printed_page": source.get("printed_page"),
            }
        ],
    }


if __name__ == "__main__":
    result = answer_question(
        question="What are the symptoms of Fusarium wilt in cotton?",
        crop="cotton",
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))