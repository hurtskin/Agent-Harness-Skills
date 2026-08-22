"""PT sandbox — stdlib random search only (no Hypothesis required)."""

from __future__ import annotations

import random
import string
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from register_domain import (  # noqa: E402
    ALLOWED,
    EVENTS,
    DomainError,
    UserStatus,
    UserStore,
    apply_transition,
    is_valid_email,
    is_valid_password,
)

N = 40


def gen_valid_email(rng: random.Random) -> str:
    user = "".join(rng.choice(string.ascii_lowercase) for _ in range(rng.randint(3, 12)))
    domain = "".join(rng.choice(string.ascii_lowercase) for _ in range(rng.randint(3, 8)))
    email = f"{user}@{domain}.com"
    assert is_valid_email(email)
    return email


def gen_valid_password(rng: random.Random) -> str:
    letters = "".join(rng.choice(string.ascii_letters) for _ in range(6))
    digits = "".join(rng.choice(string.digits) for _ in range(3))
    password = letters + digits
    assert is_valid_password(password)
    return password


class TestPReg01Stdlib(unittest.TestCase):
    def test_new_email_becomes_pending(self) -> None:
        rng = random.Random(101)
        for _ in range(N):
            store = UserStore()
            email = gen_valid_email(rng)
            password = gen_valid_password(rng)
            r = store.register(email, password)
            self.assertEqual(r.http, 201)
            assert r.user is not None
            self.assertEqual(r.user.status, UserStatus.PENDING_VERIFICATION)


class TestPReg03Stdlib(unittest.TestCase):
    def test_transition_table(self) -> None:
        rng = random.Random(103)
        for _ in range(N):
            status = rng.choice(list(UserStatus))
            event = rng.choice(EVENTS)
            key = (status, event)
            if key in ALLOWED:
                self.assertEqual(apply_transition(status, event), ALLOWED[key])
            else:
                with self.assertRaises(DomainError):
                    apply_transition(status, event)


if __name__ == "__main__":
    unittest.main()
