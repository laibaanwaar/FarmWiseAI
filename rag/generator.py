
import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_groq import ChatGroq

from rag.retriever import retrieve_chunks


# Load .env whenever this module is imported
PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")


def generate_answer(question: str, passage: str) -> str:
    """Generate an English answer from one retrieved passage."""

    model = ChatGroq(
        model=os.environ["GROQ_MODEL"],
        temperature=0
    )

    response = model.invoke([
        (
            "system",
            "Answer in English using only the supplied handbook passage. "
            "Include only details relevant to the question. "
            "Correct obvious word breaks from PDF extraction. "
            "If the passage does not answer the question, say so.",
        ),
        ("human", f"Question:\n{question}\n\nHandbook passage:\n{passage}"),
    ])

    return response.content.strip()


def generate_urdu_answer(question: str, passage: str) -> str:
    """Generate an Urdu answer using the retrieved handbook passage."""

    model = ChatGroq(
        model=os.environ["GROQ_MODEL"],
        temperature=0
    )

    response = model.invoke([
        (

        "system",
        "You are a helpful agricultural assistant for Pakistani farmers. "
        "Answer in simple, natural Pakistani Urdu using Urdu script. "
        "Use ONLY the supplied handbook passage. "
        "Do not invent facts or add information from outside the passage. "
        "Do not give diagnostic conclusions, recommendations, or advice "
        "unless they are explicitly stated in the supplied passage. "
        "Do not add introductory or concluding claims beyond the passage. "
        "If the passage does not answer the question, "
        "return exactly: INSUFFICIENT_CONTEXT. "
        "Correct obvious word breaks and spelling errors from PDF extraction. "
        "Translate technical agricultural terms into commonly understood Urdu. "
        "For example, translate 'cotton bolls' as 'کپاس کی ٹینڈیاں'. "
        "Keep important English technical terms in parentheses when useful. "
        "Use short sentences and clear bullet points. "
        "Do not use Hindi vocabulary or Devanagari script. "
        "Do not generate page numbers or citations. "
        "Use natural Urdu grammar and correct masculine/feminine agreement. "
        "Translate 'water-soaked spots' as 'پانی میں بھیگے ہوئے دھبے'. "
        "Translate 'blights' as 'جھلساؤ'. "
        "Translate 'mold/fungal growth' as 'پھپھوندی کی تہہ'. "
        "Translate 'as the plant approaches maturity' as 'پودے کی پختگی کے قریب'."

        
        ),
        (
            "human",
            f"Question:\n{question}\n\n"
            f"Handbook passage:\n{passage}"
        ),
    ])

    return response.content.strip()
def answer_question(question: str, crop: str, language: str = "english") -> dict:
    """Retrieve relevant handbook context and generate an answer."""

    matches = retrieve_chunks(question, crop=crop, top_k=1)

    if not matches:
        return {
            "answer": "INSUFFICIENT_CONTEXT",
            "source": None
        }

    match = matches[0]
    passage = match["text"]

    if language.lower() == "urdu":
        answer = generate_urdu_answer(question, passage)
    elif language.lower() == "english":
        answer = generate_answer(question, passage)
    else:
        raise ValueError("Language must be 'english' or 'urdu'.")

    if answer.strip() == "INSUFFICIENT_CONTEXT":
        return {
            "answer": answer,
            "source": None
        }

    return {
        "answer": answer,
        "source": match["metadata"]
    }


def ask_farmwise(question: str, crop: str, language: str = "english") -> None:
    """Print the answer and its handbook source."""

    result = answer_question(question, crop, language)

    print(f"\nAnswer:\n{result['answer']}")

    if result["source"]:
        source = result["source"]
        print(
            f"\nSource: {source['document_title']}, "
            f"PDF page {source['pdf_page']}"
        )

if __name__ == "__main__":

    question = "What are the symptoms of Fusarium wilt in cotton?"

    matches = retrieve_chunks(question, crop="cotton", top_k=1)

    if not matches:
        print("No handbook passage found.")

    else:
        match = matches[0]

        answer = generate_answer(question, match["text"])
        source = match["metadata"]

        print(f"\nAnswer:\n{answer}")
        print(
            f"\nSource: {source['document_title']}, "
            f"PDF page {source['pdf_page']}"
        )
