import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_groq import ChatGroq

from rag.retriever import retrieve_chunks


def generate_answer(question: str, passage: str) -> str:
    """Generate an English answer from one retrieved passage."""
    model = ChatGroq(model=os.environ["GROQ_MODEL"])

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

    return response.text.strip()


if __name__ == "__main__":
    project_root = Path(__file__).resolve().parents[1]
    load_dotenv(project_root / ".env")

    question = "What are the symptoms of Fusarium wilt in cotton?"
    matches = retrieve_chunks(question, crop="cotton", top_k=1)

    if not matches:
        print("No handbook passage found.")
    else:
        match = matches[0]
        answer = generate_answer(question, match["text"])
        source = match["metadata"]

        print(f"\nAnswer:\n{answer}")
        print(f"\nSource: {source['document_title']}, PDF page {source['pdf_page']}")