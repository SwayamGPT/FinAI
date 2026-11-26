from datetime import date

import pytest
from pydantic import ValidationError

from models import ExpenseModel, RegisterModel, UserAuth, GoalModel
from utils.passwords import hash_password, verify_password


def test_password_roundtrip_and_long_password():
    h = hash_password("correct horse")
    assert verify_password("correct horse", h)
    assert not verify_password("wrong", h)
    long_pw = "x" * 200  # bcrypt>=5 raises on >72 bytes without truncation
    assert verify_password(long_pw, hash_password(long_pw))


def test_expense_date_defaults_to_today():
    assert ExpenseModel(title="Tea", amount=10).date == date.today().isoformat()


def test_invalid_values_rejected():
    with pytest.raises(ValidationError):
        ExpenseModel(title="Tea", amount=-5)
    with pytest.raises(ValidationError):
        GoalModel(name="x", target_amount=10, target_date="not-a-date", priority="High")
    with pytest.raises(ValidationError):
        RegisterModel(username="bob", password="short")


def test_login_model_is_lenient_for_legacy_accounts():
    assert UserAuth(username=" bob ", password="abc").username == "bob"
