from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from pymongo.errors import PyMongoError

from backend.database import mongo_client
from backend.database import database
from backend.repositories.auth_token_repository import AuthTokenRepository
from backend.repositories.auth_session_repository import AuthSessionRepository
from backend.repositories.chat_repository import ChatRepository
from backend.repositories.user_repository import UserRepository
from backend.routes.router import router
from backend.services.auth_service import AuthService
from backend.services.chat_service import ChatService
from backend.services.email_service import send_verification_email

app = FastAPI(title="Farm Wise AI API")
app.include_router(router)
user_repository = UserRepository(database["users"])
auth_session_repository = AuthSessionRepository(database["auth_sessions"])
app.state.auth_service = AuthService(
    user_repository,
    AuthTokenRepository(database["auth_tokens"]),
    send_verification_email,
    auth_session_repository,
)
app.state.user_repository = user_repository
app.state.auth_sessions = auth_session_repository
app.state.chat_service = ChatService(ChatRepository(database["conversations"]))


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    # Pydantic error objects may include submitted values; never echo them.
    from fastapi.responses import JSONResponse
    return JSONResponse(status_code=422, content={"detail": "Invalid request."})


@app.get("/health")
def health():
    try:
        mongo_client.admin.command("ping")
    except PyMongoError as exc:
        raise HTTPException(status_code=503, detail="MongoDB is unavailable") from exc

    return {"api": "ok", "mongodb": "connected"}
