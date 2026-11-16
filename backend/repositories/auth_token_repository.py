from datetime import datetime, timezone

from backend.models.auth_token import email_otp_document


class AuthTokenRepository:
    def __init__(self, collection):
        self.collection = collection
        self._indexes_ready = False

    def _ensure_indexes(self):
        if not self._indexes_ready:
            self.collection.create_index("otp_digest", unique=True, name="uniq_email_otp_digest")
            self.collection.create_index("expires_at", expireAfterSeconds=0, name="ttl_auth_token")
            self._indexes_ready = True

    def store(self, user_id, otp_digest, ttl_seconds):
        self._ensure_indexes()
        self.collection.insert_one(email_otp_document(user_id, otp_digest, ttl_seconds))

    def consume(self, otp_digest, user_id):
        self._ensure_indexes()
        return self.collection.find_one_and_delete({
            "otp_digest": otp_digest,
            "user_id": user_id,
            "expires_at": {"$gt": datetime.now(timezone.utc)},
        })

    def delete_for_user(self, user_id):
        self._ensure_indexes()
        self.collection.delete_many({"user_id": user_id, "purpose": "email_verification_otp"})
