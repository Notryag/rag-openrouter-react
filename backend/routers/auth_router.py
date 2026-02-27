from typing import Callable

from fastapi import APIRouter, Depends, HTTPException

from schemas.api import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from services.auth_service import AuthService


def create_auth_router(
    auth_service: AuthService,
    get_current_user: Callable = None,
) -> APIRouter:
    router = APIRouter(prefix="/auth", tags=["auth"])

    @router.post("/register", response_model=UserResponse)
    def register(payload: RegisterRequest):
        username = payload.username.strip()
        if not username:
            raise HTTPException(status_code=400, detail="Username is required")
        created = auth_service.register_user(username, payload.password)
        return UserResponse(id=created["id"], username=created["username"])

    @router.post("/login", response_model=TokenResponse)
    def login(payload: LoginRequest):
        username = payload.username.strip()
        result = auth_service.login_user(username, payload.password)
        return TokenResponse(
            access_token=result["access_token"],
            username=result["username"],
        )

    @router.get("/me", response_model=UserResponse)
    def me(user=Depends(get_current_user)):
        return UserResponse(id=user["id"], username=user["username"])

    return router
