import asyncio

from fastapi import HTTPException, Request, Response
from pymongo.errors import PyMongoError

from backend.core.security import OTPSecretNotConfigured
from backend.serializers.auth_serializer import (
    LoginRequest, RefreshRequest, ResendVerificationRequest, SignupRequest,
    SignupResponse, UserProfileResponse, VerifyEmailRequest,
)
from backend.services.auth_service import (
    EmailNotVerified, InvalidCredentials, InvalidRefreshToken,
    InvalidVerificationCode, RateLimitExceeded,
)


GENERIC_RESPONSE = "If the address can receive verification, instructions will be sent shortly."


async def signup_controller(request: Request, payload: SignupRequest, service):
    try:
        await asyncio.to_thread(
            service.signup, payload.name, str(payload.email).lower(), payload.password,
            request.client.host if request.client else "unknown",
        )
    except RateLimitExceeded:
        raise HTTPException(status_code=429, detail="Too many requests. Try again later.")
    except PyMongoError:
        raise HTTPException(status_code=503, detail="Service temporarily unavailable.")
    except OTPSecretNotConfigured:
        raise HTTPException(status_code=503, detail="Service temporarily unavailable.")
    return SignupResponse(message=GENERIC_RESPONSE)


async def resend_verification_controller(
    request: Request, payload: ResendVerificationRequest, service
):
    try:
        await asyncio.to_thread(
            service.resend_verification, str(payload.email).lower(),
            request.client.host if request.client else "unknown",
        )
    except RateLimitExceeded:
        raise HTTPException(status_code=429, detail="Too many requests. Try again later.")
    except PyMongoError:
        raise HTTPException(status_code=503, detail="Service temporarily unavailable.")
    except OTPSecretNotConfigured:
        raise HTTPException(status_code=503, detail="Service temporarily unavailable.")
    return SignupResponse(message=GENERIC_RESPONSE)


async def verify_email_controller(request: Request, payload: VerifyEmailRequest, service):
    try:
        await asyncio.to_thread(
            service.verify_email, str(payload.email).lower(), payload.otp,
            request.client.host if request.client else "unknown",
        )
    except RateLimitExceeded:
        raise HTTPException(status_code=429, detail="Too many verification attempts. Try again later.")
    except InvalidVerificationCode:
        raise HTTPException(status_code=400, detail="Invalid or expired verification code.")
    except PyMongoError:
        raise HTTPException(status_code=503, detail="Service temporarily unavailable.")
    except OTPSecretNotConfigured:
        raise HTTPException(status_code=503, detail="Service temporarily unavailable.")
    return {"message": "Email verified."}


async def login_controller(request: Request, payload: LoginRequest, service):
    try:
        return await asyncio.to_thread(
            service.login, str(payload.email).lower(), payload.password,
            request.client.host if request.client else "unknown",
        )
    except RateLimitExceeded:
        raise HTTPException(status_code=429, detail="Too many login attempts. Try again later.")
    except InvalidCredentials:
        raise HTTPException(
            status_code=401, detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except EmailNotVerified:
        raise HTTPException(status_code=403, detail={"code": "EMAIL_NOT_VERIFIED"})
    except (PyMongoError, OTPSecretNotConfigured):
        raise HTTPException(status_code=503, detail="Service temporarily unavailable.")


async def refresh_controller(payload: RefreshRequest, service):
    try:
        return await asyncio.to_thread(service.refresh, payload.refresh_token)
    except InvalidRefreshToken:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token.")
    except (PyMongoError, OTPSecretNotConfigured):
        raise HTTPException(status_code=503, detail="Service temporarily unavailable.")


async def me_controller(current):
    user = current["user"]
    return UserProfileResponse(
        id=str(user["_id"]), name=user["name"], email=user["email"],
        role=user["role"], email_verified=bool(user.get("email_verified", False)),
    )


async def logout_controller(current, service):
    try:
        await asyncio.to_thread(service.logout, current["session_id"])
    except PyMongoError:
        raise HTTPException(status_code=503, detail="Service temporarily unavailable.")
    return Response(status_code=204)
