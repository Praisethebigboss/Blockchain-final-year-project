import pytest
import json
from pathlib import Path
from unittest.mock import patch
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

import auth


class TestPasswordHashing:
    """Tests for password hashing functions."""

    def test_hash_password_returns_string(self):
        """Test hash_password returns a string."""
        result = auth.hash_password("test123")
        assert isinstance(result, str)

    def test_verify_password_correct(self):
        """Test verifying correct password."""
        password = "test123"
        hashed = auth.hash_password(password)
        result = auth.verify_password(password, hashed)
        assert result is True

    def test_verify_password_incorrect(self):
        """Test verifying incorrect password."""
        hashed = auth.hash_password("correct")
        result = auth.verify_password("incorrect", hashed)
        assert result is False

    def test_hash_password_is_bcrypt(self):
        """Test that hash uses bcrypt."""
        hashed = auth.hash_password("test")
        assert hashed.startswith("$2b$") or hashed.startswith("$2a$")


class TestUserManagement:
    """Tests for user management functions."""

    @pytest.fixture
    def temp_users_file(self, tmp_path):
        """Create a temporary users file."""
        users_file = tmp_path / "users.json"
        with patch("auth.USERS_FILE", users_file):
            yield users_file

    def test_load_users_creates_file(self, temp_users_file):
        """Test that load_users creates file if missing."""
        with patch("auth.USERS_FILE", temp_users_file):
            users = auth.load_users()
            assert isinstance(users, dict)
            assert temp_users_file.exists()

    def test_load_users_with_existing(self, temp_users_file):
        """Test loading existing users."""
        test_users = {"admin": {"password_hash": "hash", "institution": "Test"}}
        with open(temp_users_file, "w") as f:
            json.dump(test_users, f)
        
        with patch("auth.USERS_FILE", temp_users_file):
            users = auth.load_users()
            assert "admin" in users

    def test_save_users(self, temp_users_file):
        """Test saving users."""
        test_users = {"admin": {"password_hash": "hash", "institution": "Test"}}
        
        with patch("auth.USERS_FILE", temp_users_file):
            auth.save_users(test_users)
            with open(temp_users_file) as f:
                loaded = json.load(f)
            assert loaded["admin"]["institution"] == "Test"


class TestAuthentication:
    """Tests for authentication function."""

    def test_authenticate_success(self):
        """Test successful authentication."""
        test_users = {
            "admin": {
                "password_hash": auth.hash_password("admin123"),
                "institution": "Admin"
            }
        }
        
        with patch("auth.load_users", return_value=test_users):
            result = auth.authenticate("admin", "admin123")
            assert result is not None
            assert result["username"] == "admin"

    def test_authenticate_wrong_password(self):
        """Test authentication with wrong password."""
        test_users = {
            "admin": {
                "password_hash": auth.hash_password("admin123"),
                "institution": "Admin"
            }
        }
        
        with patch("auth.load_users", return_value=test_users):
            result = auth.authenticate("admin", "wrong")
            assert result is None

    def test_authenticate_unknown_user(self):
        """Test authentication with unknown user."""
        test_users = {
            "admin": {
                "password_hash": auth.hash_password("admin123"),
                "institution": "Admin"
            }
        }
        
        with patch("auth.load_users", return_value=test_users):
            result = auth.authenticate("unknown", "password")
            assert result is None


class TestDefaultUsers:
    """Tests for default user creation."""

    @pytest.fixture
    def temp_users_file(self, tmp_path):
        """Create a temporary users file."""
        users_file = tmp_path / "users.json"
        
        with patch("auth.USERS_FILE", users_file):
            yield users_file

    def test_ensure_users_file_creates_default(self, temp_users_file):
        """Test that _ensure_users_file creates default admin user."""
        auth._ensure_users_file()
        
        with open(temp_users_file) as f:
            users = json.load(f)
        
        assert "admin" in users
        assert users["admin"]["institution"] == "Admin"


def test_auth_module_import():
    """Test that auth module can be imported."""
    import auth
    assert auth is not None


def test_auth_functions():
    """Test that auth functions exist."""
    assert callable(auth.hash_password)
    assert callable(auth.verify_password)
    assert callable(auth.authenticate)
    assert callable(auth.load_users)
    assert callable(auth.save_users)