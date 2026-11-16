import asyncio
from datetime import datetime, timezone

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pymongo.errors import PyMongoError

from backend.core.security import hash_token

_bearer = HTTPBearer(auto_error=False)


def _as_utc(value):
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)


def _load_current_session(request, token):
    digest = hash_token(token)
    now = datetime.now(timezone.utc)
    session = request.app.state.auth_sessions.find_active_by_access_hash(digest, now)
    if not session:
        raise InvalidAccessToken
    if _as_utc(session["access_expires_at"]) <= now:
        raise AccessTokenExpired
    user = request.app.state.user_repository.find_by_id(session["user_id"])
    if not user:
        raise InvalidAccessToken
    return {"user": user, "session_id": session["_id"]}


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
):
    if not credentials or credentials.scheme.casefold() != "bearer":
        raise HTTPException(
            status_code=401, detail={"code": "INVALID_ACCESS_TOKEN"},
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        current = await asyncio.to_thread(_load_current_session, request, credentials.credentials)
    except AccessTokenExpired:
        raise HTTPException(
            status_code=401, detail={"code": "ACCESS_TOKEN_EXPIRED"},
            headers={"WWW-Authenticate": "Bearer"},
        )
    except (InvalidAccessToken, UnicodeError):
        raise HTTPException(
            status_code=401, detail={"code": "INVALID_ACCESS_TOKEN"},
            headers={"WWW-Authenticate": "Bearer"},
        )
    except PyMongoError:
        raise HTTPException(status_code=503, detail="Service temporarily unavailable.")
    return current


class InvalidAccessToken(Exception):
    pass


class AccessTokenExpired(Exception):
    pass
