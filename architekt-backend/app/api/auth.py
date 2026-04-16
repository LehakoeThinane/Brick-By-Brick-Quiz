from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserPublic
from app.services.auth_service import authenticate_user, create_token_for_user, get_current_user, register_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register_endpoint(payload: RegisterRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = register_user(db, payload)
    token, expires_in = create_token_for_user(user)
    return TokenResponse(access_token=token, expires_in=expires_in, user=UserPublic.model_validate(user))


@router.post("/login", response_model=TokenResponse)
def login_endpoint(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = authenticate_user(db, payload)
    token, expires_in = create_token_for_user(user)
    return TokenResponse(access_token=token, expires_in=expires_in, user=UserPublic.model_validate(user))


@router.get("/me", response_model=UserPublic)
def me_endpoint(current_user=Depends(get_current_user)) -> UserPublic:
    return UserPublic.model_validate(current_user)
