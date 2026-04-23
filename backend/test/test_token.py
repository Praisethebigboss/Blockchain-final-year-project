import pytest
import time
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from storage_service import (
    store_student_token,
    get_token,
    invalidate_token,
    validate_student_token,
    TOKENS_DB,
)


class TestStudentTokenStorage:
    """Tests for student token storage functions."""

    def setup_method(self):
        if TOKENS_DB.exists():
            with open(TOKENS_DB, "r") as f:
                self.original_db = json.load(f)
        else:
            self.original_db = None

    def teardown_method(self):
        if hasattr(self, "original_db"):
            with open(TOKENS_DB, "w") as f:
                json.dump(self.original_db or {}, f, indent=2)
        elif TOKENS_DB.exists():
            TOKENS_DB.unlink()

    def test_store_student_token(self):
        """Test storing a student token."""
        result = store_student_token("abc123", "token123", "student@test.com")
        
        assert result["hash"] == "abc123"
        assert result["token"] == "token123"
        assert "expires_at" in result

    def test_get_token(self):
        """Test retrieving a token."""
        store_student_token("hash456", "token456", "student@test.com")
        
        token_data = get_token("hash456")
        assert token_data is not None
        assert token_data["token"] == "token456"
        assert token_data["student_email"] == "student@test.com"
        assert token_data["used"] is False

    def test_get_token_not_found(self):
        """Test retrieving a non-existent token."""
        token_data = get_token("nonexistent")
        assert token_data is None

    def test_validate_valid_token(self):
        """Test validating a valid token."""
        store_student_token("validhash", "validtoken")
        
        result = validate_student_token("validhash", "validtoken")
        assert result["valid"] is True
        assert result["error"] is None

    def test_validate_invalid_token(self):
        """Test validating with wrong token."""
        store_student_token("hash789", "correcttoken")
        
        result = validate_student_token("hash789", "wrongtoken")
        assert result["valid"] is False
        assert result["error"] == "Invalid token"

    def test_validate_token_not_found(self):
        """Test validating non-existent token."""
        result = validate_student_token("nonexistent", "anytoken")
        assert result["valid"] is False
        assert result["error"] == "Token not found"

    def test_validate_used_token(self):
        """Test validating a token that has been used."""
        store_student_token("usedhash", "usedtoken")
        invalidate_token("usedhash")
        
        result = validate_student_token("usedhash", "usedtoken")
        assert result["valid"] is False
        assert result["error"] == "Link already used"

    def test_invalidate_token(self):
        """Test invalidating a token."""
        store_student_token("invalhash", "invaltoken")
        
        result = invalidate_token("invalhash")
        assert result is True
        
        token_data = get_token("invalhash")
        assert token_data["used"] is True

    def test_invalidate_nonexistent_token(self):
        """Test invalidating a non-existent token."""
        result = invalidate_token("nonexistent")
        assert result is False


class TestTokenExpiry:
    """Tests for token expiry functionality."""

    def setup_method(self):
        if TOKENS_DB.exists():
            TOKENS_DB.unlink()

    def teardown_method(self):
        if TOKENS_DB.exists():
            TOKENS_DB.unlink()

    def test_token_has_expiry(self):
        """Test that tokens have expiry timestamps."""
        result = store_student_token("hash", "token", "email@test.com")
        
        token_data = get_token("hash")
        assert "expires_at" in token_data
        assert "created_at" in token_data
        assert token_data["expires_at"] > token_data["created_at"]
