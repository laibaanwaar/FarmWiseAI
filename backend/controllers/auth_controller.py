import asyncio

from fastapi import HTTPException, Request
from pymongo.errors import PyMongoError

from backend.serializers.auth_serializer import (
    ResendVerificationRequest, SignupRequest, SignupResponse,
)
from backend.services.auth_service import RateLimitExceeded


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
    return SignupResponse(message=GENERIC_RESPONSE)
