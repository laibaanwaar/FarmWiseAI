from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from pymongo.errors import PyMongoError

from backend.database import mongo_client
from backend.database import database
from backend.repositories.auth_token_repository import AuthTokenRepository
from backend.repositories.user_repository import UserRepository
from backend.routes.router import router
from backend.services.auth_service import AuthService
from backend.services.email_service import send_verification_email

app = FastAPI(title="Farm Wise AI API")
app.include_router(router)
app.state.auth_service = AuthService(
    UserRepository(database["users"]),
    AuthTokenRepository(database["auth_tokens"]),
    send_verification_email,
)


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
