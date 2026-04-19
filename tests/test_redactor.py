"""Tests for logwatch.redactor."""
import pytest
from logwatch.redactor import Redactor, REDACT_PLACEHOLDER, default_redactor


@pytest.fixture
def redactor() -> Redactor:
    return Redactor()


def _entry(message="hello", fields=None):
    return {"message": message, "level": "info", "fields": fields or {}}


def test_redact_value_leaves_clean_string(redactor):
    assert redactor.redact_value("just a normal log line") == "just a normal log line"


def test_redact_value_masks_password_param(redactor):
    result = redactor.redact_value("login password=hunter2 ok")
    assert "hunter2" not in result
    assert REDACT_PLACEHOLDER in result


def test_redact_value_masks_token_param(redactor):
    result = redactor.redact_value("auth token=abc123xyz")
    assert "abc123xyz" not in result


def test_redact_value_masks_card_number(redactor):
    result = redactor.redact_value("card 1234-5678-9012-3456 used")
    assert "1234-5678-9012-3456" not in result
    assert REDACT_PLACEHOLDER in result


def test_redact_fields_masks_sensitive_key(redactor):
    result = redactor.redact_fields({"password": "s3cr3t", "user": "alice"})
    assert result["password"] == REDACT_PLACEHOLDER
    assert result["user"] == "alice"


def test_redact_fields_masks_token_key(redactor):
    result = redactor.redact_fields({"token": "mytoken", "level": "info"})
    assert result["token"] == REDACT_PLACEHOLDER


def test_redact_fields_case_insensitive_key(redactor):
    result = redactor.redact_fields({"Password": "oops"})
    assert result["Password"] == REDACT_PLACEHOLDER


def test_redact_entry_cleans_message(redactor):
    entry = _entry(message="user secret=topsecret logged in")
    result = redactor.redact_entry(entry)
    assert "topsecret" not in result["message"]


def test_redact_entry_cleans_fields(redactor):
    entry = _entry(fields={"api_key": "key-xyz", "host": "localhost"})
    result = redactor.redact_entry(entry)
    assert result["fields"]["api_key"] == REDACT_PLACEHOLDER
    assert result["fields"]["host"] == "localhost"


def test_redact_entry_preserves_level(redactor):
    entry = _entry()
    result = redactor.redact_entry(entry)
    assert result["level"] == "info"


def test_redact_entry_does_not_mutate_original(redactor):
    entry = _entry(fields={"password": "secret"})
    redactor.redact_entry(entry)
    assert entry["fields"]["password"] == "secret"


def test_default_redactor_returns_redactor():
    r = default_redactor()
    assert isinstance(r, Redactor)


def test_custom_sensitive_keys():
    r = Redactor(sensitive_keys=["pin"])
    result = r.redact_fields({"pin": "1234", "name": "bob"})
    assert result["pin"] == REDACT_PLACEHOLDER
    assert result["name"] == "bob"
