from datetime import datetime, timezone


def auth_session_document(
    user_id, access_token_hash, refresh_token_hash, access_expires_at,
    session_expires_at,
):
    return {
        "user_id": user_id,
        "access_token_hash": access_token_hash,
        "refresh_token_hash": refresh_token_hash,
        "rotated_refresh_token_hashes": [],
        "access_expires_at": access_expires_at,
        "session_expires_at": session_expires_at,
        "created_at": datetime.now(timezone.utc),
        "revoked": False,
        "revoked_at": None,
    }
