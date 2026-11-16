from datetime import datetime, timedelta, timezone


def email_otp_document(user_id, otp_digest, ttl_seconds):
    now = datetime.now(timezone.utc)
    return {
        "user_id": user_id,
        "otp_digest": otp_digest,
        "created_at": now,
        "expires_at": now + timedelta(seconds=ttl_seconds),
        "purpose": "email_verification_otp",
    }
