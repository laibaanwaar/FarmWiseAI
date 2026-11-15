import chromadb

from rag.embeddings import get_embedding_model
from rag.index import CHROMA_DIR, COLLECTION_NAME


def retrieve_chunks(question: str, crop: str, top_k: int = 3) -> list[dict]:
    """Find relevant passages for a crop and return their source metadata."""
    question = question.strip()
    crop = crop.strip().lower()

    if not question or not crop:
        raise ValueError("Question and crop are required.")
    if top_k < 1:
        raise ValueError("top_k must be at least 1.")

    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    collection = client.get_collection(name=COLLECTION_NAME)

    total_records = collection.count()
    if total_records == 0:
        return []

    query_vector = get_embedding_model().embed_query(question)
    results = collection.query(
        query_embeddings=[query_vector],
        where={"crop": crop},
        n_results=min(top_k, total_records),
        include=["documents", "metadatas"],
    )

    documents = results["documents"] or [[]]
    metadatas = results["metadatas"] or [[]]

    return [
        {"text": text, "metadata": metadata}
        for text, metadata in zip(documents[0], metadatas[0])
    ]


if __name__ == "__main__":
    matches = retrieve_chunks(
        question="What are the symptoms of Fusarium wilt in cotton?",
        crop="cotton",
    )

    if not matches:
        print("No passages found for the selected crop.")

    for rank, match in enumerate(matches, start=1):
        source = match["metadata"]
        print(f"\nResult {rank} — {source['disease']}")
        print(f"Crop: {source['crop']} | PDF page: {source['pdf_page']}")
        print(match["text"])