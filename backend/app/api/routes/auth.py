"""
app/api/routes/auth.py

Authentication endpoints: register, login, me.
JWT access token issued on login.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_db_session, get_current_user
from app.core.security import verify_password, create_access_token
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, UserResponse, TokenWithUser
from app.services import user_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
)
def register(
    payload: UserCreate,
    db: Session = Depends(get_db_session),
) -> UserResponse:
    """
    Create a new user account. Returns the created user (no password).
    - **email** must be unique
    - **password** must be ≥ 8 characters
    - **role** defaults to `finance_user`
    """
    try:
        user = user_service.create_user(db, payload)
    except user_service.DuplicateEmailError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )
    except ValueError as exc:
        msg = str(exc)
        if "already registered" in msg.lower() or "already exists" in msg.lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this email already exists.",
            )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)
    except Exception as exc:
        logger.error("Unexpected error during registration: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="A server error occurred. Please try again later.",
        )
    return user


@router.post(
    "/login",
    response_model=TokenWithUser,
    summary="Authenticate and receive a JWT access token",
)
def login(
    payload: UserLogin,
    db: Session = Depends(get_db_session),
) -> TokenWithUser:
    """
    Authenticate with email + password.
    Returns a Bearer JWT token and the authenticated user profile.
    """
    user = user_service.get_user_by_email(db, payload.email)
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive",
        )

    token = create_access_token(
        subject=str(user.id),
        extra_claims={"role": user.role.value, "email": user.email},
    )
    logger.info("User %s logged in", user.id)
    return TokenWithUser(
        access_token=token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Return the currently authenticated user",
)
def me(current_user: User = Depends(get_current_user)) -> UserResponse:
    """Return the profile of the currently authenticated user."""
    return current_user
