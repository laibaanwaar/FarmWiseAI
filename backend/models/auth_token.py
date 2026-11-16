from datetime import datetime, timedelta, timezone


def verification_token_document(user_id, token_hash, ttl_seconds):
    now = datetime.now(timezone.utc)
    return {
        "user_id": user_id,
        "token_hash": token_hash,
        "created_at": now,
        "expires_at": now + timedelta(seconds=ttl_seconds),
        "purpose": "email_verification",
    }
