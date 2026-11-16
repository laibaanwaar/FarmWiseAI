from datetime import datetime, timezone


def new_user_document(name, email, password_hash):
    return {
        "name": name,
        "email": email,
        "password_hash": password_hash,
        "role": "user",
        "email_verified": False,
        "created_at": datetime.now(timezone.utc),
    }
