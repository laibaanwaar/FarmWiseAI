import json
from pathlib import Path

import chromadb

from rag.embeddings import get_embedding_model


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CHUNKS_FILE = PROJECT_ROOT / "data" / "processed" / "handbook_final" / "chunks.jsonl"
CHROMA_DIR = PROJECT_ROOT / "data" / "chroma"
COLLECTION_NAME = "farmwise_cotton_symptoms"


def load_documents(path: Path = CHUNKS_FILE) -> list[dict]:
    """Read cotton disease rows and keep their PDF citation metadata."""
    if not path.is_file():
        raise FileNotFoundError(f"Run PDF preprocessing first. Missing file: {path}")

    documents = []

    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue

            record = json.loads(line)

            if record.get("content_type") != "table_row" or record.get("crop") != "cotton":
                continue

            text = record["text"].strip()
            if not text:
                raise ValueError(f"Empty searchable text on JSONL line {line_number}")

            metadata = {
                "crop": record["crop"],
                "disease": record["disease"],
                "document_title": record["document_title"],
                "pdf_page": record["pdf_page"],
                "content_type": record["content_type"],
            }

            if record.get("printed_page") is not None:
                metadata["printed_page"] = record["printed_page"]

            documents.append({
                "id": record["id"],
                "text": text,
                "metadata": metadata,
            })

    if not documents:
        raise ValueError(f"No cotton disease rows found in {path}")

    return documents


def build_index() -> int:
    """Generate embeddings and save the selected records in local ChromaDB."""
    documents = load_documents()
    texts = [document["text"] for document in documents]

    embedding_model = get_embedding_model()
    vectors = embedding_model.embed_documents(texts)

    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    collection = client.get_or_create_collection(name=COLLECTION_NAME)

    collection.upsert(
        ids=[document["id"] for document in documents],
        documents=texts,
        embeddings=vectors,
        metadatas=[document["metadata"] for document in documents],
    )

    print(f"Indexed {len(documents)} records into {COLLECTION_NAME}")
    print(f"Chroma directory: {CHROMA_DIR}")
    return collection.count()


if __name__ == "__main__":
    total = build_index()
    print(f"Total records in collection: {total}")