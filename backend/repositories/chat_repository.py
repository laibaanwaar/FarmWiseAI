from bson import ObjectId
from pymongo import ASCENDING, DESCENDING

from backend.models.conversation import conversation_document


class ChatRepository:
    def __init__(self, collection):
        self.collection = collection
        self._index_ready = False

    def _ensure_index(self):
        if not self._index_ready:
            self.collection.create_index(
                [("owner_id", ASCENDING), ("updated_at", DESCENDING)],
                name="owner_recent_conversations",
            )
            self._index_ready = True

    def create(self, owner_id, question, answer, citations, status, crop):
        self._ensure_index()
        document = conversation_document(owner_id, question, answer, citations, status, crop)
        result = self.collection.insert_one(document)
        document["_id"] = result.inserted_id
        return document

    def append_message(self, owner_id, conversation_id, message, crop):
        self._ensure_index()
        result = self.collection.update_one(
            {"_id": ObjectId(conversation_id), "owner_id": owner_id},
            {
                "$push": {"messages": message},
                "$set": {"updated_at": message["created_at"], "crop": crop},
                "$inc": {"message_count": 1},
            },
        )
        return result.matched_count == 1

    def list_for_user(self, owner_id, offset, limit):
        self._ensure_index()
        cursor = (self.collection.find({"owner_id": owner_id}, {"messages": 0})
                  .sort([("updated_at", DESCENDING), ("_id", DESCENDING)])
                  .skip(offset).limit(limit))
        return [
            {
                "conversation_id": str(row["_id"]),
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
                "message_count": row["message_count"],
            }
            for row in cursor
        ]

    def get_for_user(self, owner_id, conversation_id):
        self._ensure_index()
        row = self.collection.find_one({
            "_id": ObjectId(conversation_id),
            "owner_id": owner_id,
        })
        if not row:
            return None
        return {
            "conversation_id": str(row["_id"]),
            "owner_id": row["owner_id"],
            "crop": row.get("crop", "cotton"),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "messages": sorted(row.get("messages", []), key=lambda item: item["created_at"]),
            "message_count": row.get("message_count", len(row.get("messages", []))),
        }
