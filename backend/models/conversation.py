from datetime import datetime, timezone


def conversation_document(owner_id, question, answer, citations, status, crop, timestamp=None):
    created_at = timestamp or datetime.now(timezone.utc)
    message = {
        "question": question,
        "answer": answer,
        "citations": citations,
        "status": status,
        "created_at": created_at,
    }
    return {
        "owner_id": owner_id,
        "crop": crop,
        "created_at": created_at,
        "updated_at": created_at,
        "message_count": 1,
        "messages": [message],
    }
