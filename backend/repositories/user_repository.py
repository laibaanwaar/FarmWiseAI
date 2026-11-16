from pymongo.errors import DuplicateKeyError

from backend.models.user import new_user_document


class UserRepository:
    def __init__(self, collection):
        self.collection = collection
        self._index_ready = False

    def _ensure_index(self):
        if not self._index_ready:
            self.collection.create_index("email", unique=True, name="uniq_user_email")
            self._index_ready = True

    def create(self, name, email, password_hash):
        self._ensure_index()
        document = new_user_document(name, email, password_hash)
        try:
            result = self.collection.insert_one(document)
        except DuplicateKeyError:
            return None
        document["_id"] = result.inserted_id
        return document

    def find_pending_by_email(self, email):
        self._ensure_index()
        return self.collection.find_one({"email": email, "email_verified": False})

    def find_by_email(self, email):
        self._ensure_index()
        return self.collection.find_one({"email": email})

    def find_by_id(self, user_id):
        return self.collection.find_one({"_id": user_id})

    def mark_email_verified(self, user_id):
        result = self.collection.update_one(
            {"_id": user_id, "email_verified": False},
            {"$set": {"email_verified": True}},
        )
        return result.modified_count == 1
