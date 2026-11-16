from fastapi import APIRouter, Depends, Request, status

from backend.controllers.auth_controller import (
    login_controller, logout_controller, me_controller, refresh_controller,
    resend_verification_controller, signup_controller, verify_email_controller,
)
from backend.serializers.auth_serializer import (
    LoginRequest, RefreshRequest, ResendVerificationRequest, SignupRequest,
    SignupResponse, TokenResponse, UserProfileResponse, VerifyEmailRequest,
)
from backend.dependencies.auth import get_current_user

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


@router.post("/verify-email")
async def verify_email(request: Request, payload: VerifyEmailRequest):
    return await verify_email_controller(request, payload, get_auth_service(request))


@router.post("/login", response_model=TokenResponse)
async def login(request: Request, payload: LoginRequest):
    return await login_controller(request, payload, get_auth_service(request))


@router.post("/refresh", response_model=TokenResponse)
async def refresh(payload: RefreshRequest, request: Request):
    return await refresh_controller(payload, get_auth_service(request))


@router.get("/me", response_model=UserProfileResponse)
async def me(current=Depends(get_current_user)):
    return await me_controller(current)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(request: Request, current=Depends(get_current_user)):
    return await logout_controller(current, get_auth_service(request))
