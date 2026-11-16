from pymongo import ReturnDocument

from backend.models.auth_session import auth_session_document


class AuthSessionRepository:
    def __init__(self, collection):
        self.collection = collection
        self._indexes_ready = False

    def _ensure_indexes(self):
        if self._indexes_ready:
            return
        self.collection.create_index(
            "access_token_hash", unique=True, name="uniq_session_access_hash"
        )
        self.collection.create_index(
            "refresh_token_hash", unique=True, name="uniq_session_refresh_hash"
        )
        self.collection.create_index(
            "session_expires_at", expireAfterSeconds=0, name="ttl_auth_session"
        )
        self._indexes_ready = True

    def create_session(
        self, user_id, access_token_hash, refresh_token_hash,
        access_expires_at, session_expires_at,
    ):
        self._ensure_indexes()
        document = auth_session_document(
            user_id, access_token_hash, refresh_token_hash,
            access_expires_at, session_expires_at,
        )
        result = self.collection.insert_one(document)
        document["_id"] = result.inserted_id
        return document

    def find_active_by_refresh_hash(self, refresh_hash, now):
        self._ensure_indexes()
        return self.collection.find_one({
            "refresh_token_hash": refresh_hash,
            "revoked": False,
            "session_expires_at": {"$gt": now},
        })

    def rotate_refresh(
        self, session_id, old_refresh_hash, access_hash, refresh_hash,
        access_expires_at, now,
    ):
        self._ensure_indexes()
        return self.collection.find_one_and_update(
            {
                "_id": session_id,
                "refresh_token_hash": old_refresh_hash,
                "revoked": False,
                "session_expires_at": {"$gt": now},
            },
            {
                "$set": {
                    "access_token_hash": access_hash,
                    "refresh_token_hash": refresh_hash,
                    "access_expires_at": access_expires_at,
                },
                "$push": {"rotated_refresh_token_hashes": old_refresh_hash},
            },
            return_document=ReturnDocument.AFTER,
        )

    def revoke_if_reused_refresh_hash(self, refresh_hash, now):
        self._ensure_indexes()
        result = self.collection.update_one(
            {
                "rotated_refresh_token_hashes": refresh_hash,
                "revoked": False,
                "session_expires_at": {"$gt": now},
            },
            {"$set": {"revoked": True, "revoked_at": now}},
        )
        return result.modified_count == 1

    def find_active_by_access_hash(self, access_hash, now):
        self._ensure_indexes()
        return self.collection.find_one({
            "access_token_hash": access_hash,
            "revoked": False,
            "session_expires_at": {"$gt": now},
        })

    def revoke(self, session_id, now):
        self._ensure_indexes()
        result = self.collection.update_one(
            {"_id": session_id, "revoked": False},
            {"$set": {"revoked": True, "revoked_at": now}},
        )
        return result.modified_count == 1
