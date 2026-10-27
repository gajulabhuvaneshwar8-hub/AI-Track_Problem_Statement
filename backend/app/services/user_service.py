"""
app/services/user_service.py

Database operations for the User entity.
No business logic beyond what is directly needed to manage user records.
"""

from __future__ import annotations

import logging
import uuid
from typing import Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.user import UserCreate

logger = logging.getLogger(__name__)


class DuplicateEmailError(ValueError):
    """Raised when registering an email that already exists."""
    pass


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Return the User with the given email, or None."""
    return db.query(User).filter(User.email == email.lower().strip()).first()


def get_user_by_id(db: Session, user_id: uuid.UUID) -> Optional[User]:
    """Return the User with the given primary key, or None."""
    return db.get(User, user_id)


def create_user(db: Session, payload: UserCreate) -> User:
    """
    Create and persist a new User.
    Raises DuplicateEmailError if the email is already registered.
    """
    normalized_email = payload.email.lower().strip()
    if get_user_by_email(db, normalized_email):
        raise DuplicateEmailError("An account with this email already exists.")

    user = User(
        id=uuid.uuid4(),
        name=payload.name.strip(),
        email=normalized_email,
        password_hash=hash_password(payload.password),
        role=payload.role if payload.role else UserRole.finance_user,
        is_active=True,
    )
    try:
        db.add(user)
        db.commit()
        db.refresh(user)
    except IntegrityError as exc:
        db.rollback()
        logger.warning("IntegrityError on user registration for %s: %s", normalized_email, exc)
        raise DuplicateEmailError("An account with this email already exists.") from exc
    except Exception as exc:
        db.rollback()
        logger.error("Database error committing user registration for %s: %s", normalized_email, exc, exc_info=True)
        raise

    logger.info("Created user %s (role=%s)", user.id, user.role.value)
    return user


def list_assignable_users(db: Session) -> list[User]:
    """Return all active users who can be assigned reconciliation exceptions."""
    return (
        db.query(User)
        .filter(User.is_active.is_(True))
        .order_by(User.name.asc())
        .all()
    )

