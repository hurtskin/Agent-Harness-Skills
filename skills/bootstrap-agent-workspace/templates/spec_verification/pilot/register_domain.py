"""Sandbox domain for light-PBT verification (not production)."""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass
from enum import Enum


class UserStatus(str, Enum):
    PENDING_VERIFICATION = "PENDING_VERIFICATION"
    ACTIVE = "ACTIVE"
    DISABLED = "DISABLED"


class DomainError(Exception):
    def __init__(self, error_code: str, http: int, message: str = "") -> None:
        super().__init__(message or error_code)
        self.error_code = error_code
        self.http = http


_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_PASSWORD_RE = re.compile(r"^(?=.*[A-Za-z])(?=.*\d).+$")


def is_valid_email(email: str) -> bool:
    return bool(email) and len(email) <= 254 and _EMAIL_RE.match(email) is not None


def is_valid_password(password: str) -> bool:
    return 8 <= len(password) <= 128 and _PASSWORD_RE.match(password) is not None


@dataclass(frozen=True)
class User:
    user_id: str
    email: str
    password: str
    status: UserStatus


@dataclass(frozen=True)
class RegisterResult:
    http: int
    error_code: str | None
    user: User | None


class UserStore:
    def __init__(self) -> None:
        self._by_email: dict[str, User] = {}

    def email_exists(self, email: str) -> bool:
        return email.lower() in self._by_email

    def snapshot(self, email: str) -> User | None:
        return self._by_email.get(email.lower())

    def seed(self, email: str, password: str, status: UserStatus) -> User:
        if not is_valid_email(email) or not is_valid_password(password):
            raise DomainError("VALIDATION_ERROR", 422)
        user = User(
            user_id=str(uuid.uuid4()),
            email=email.lower(),
            password=password,
            status=status,
        )
        self._by_email[user.email] = user
        return user

    def register(self, email: str, password: str) -> RegisterResult:
        if not is_valid_email(email) or not is_valid_password(password):
            return RegisterResult(http=422, error_code="VALIDATION_ERROR", user=None)

        key = email.lower()
        if key in self._by_email:
            return RegisterResult(
                http=409,
                error_code="EMAIL_ALREADY_REGISTERED",
                user=None,
            )

        user = User(
            user_id=str(uuid.uuid4()),
            email=key,
            password=password,
            status=UserStatus.PENDING_VERIFICATION,
        )
        self._by_email[key] = user
        return RegisterResult(http=201, error_code=None, user=user)


ALLOWED: dict[tuple[UserStatus, str], UserStatus] = {
    (UserStatus.PENDING_VERIFICATION, "VERIFY"): UserStatus.ACTIVE,
    (UserStatus.PENDING_VERIFICATION, "EXPIRE"): UserStatus.DISABLED,
    (UserStatus.ACTIVE, "DISABLE"): UserStatus.DISABLED,
}
EVENTS = ("VERIFY", "EXPIRE", "DISABLE")


def apply_transition(status: UserStatus, event: str) -> UserStatus:
    key = (status, event)
    if key not in ALLOWED:
        raise DomainError("INVALID_TRANSITION", 400, f"{status.value}+{event}")
    return ALLOWED[key]
