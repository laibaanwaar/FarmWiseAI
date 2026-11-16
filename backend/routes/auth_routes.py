from fastapi import APIRouter, Request, status

from backend.controllers.auth_controller import (
    resend_verification_controller, signup_controller,
)
from backend.serializers.auth_serializer import (
    ResendVerificationRequest, SignupRequest, SignupResponse,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def get_auth_service(request: Request):
    return request.app.state.auth_service


@router.post("/signup", response_model=SignupResponse, status_code=status.HTTP_202_ACCEPTED)
async def signup(request: Request, payload: SignupRequest):
    return await signup_controller(request, payload, get_auth_service(request))


@router.post("/resend-verification", response_model=SignupResponse,
             status_code=status.HTTP_202_ACCEPTED)
async def resend_verification(request: Request, payload: ResendVerificationRequest):
    return await resend_verification_controller(request, payload, get_auth_service(request))
