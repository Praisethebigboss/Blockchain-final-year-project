import pytest
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

EMPLOYERS_FILE = Path(__file__).parent.parent / "data" / "employers.json"


class TestEmployerRegistration:
    """Tests for employer registration."""

    def setup_method(self):
        self.original_db = {}
        if EMPLOYERS_FILE.exists():
            with open(EMPLOYERS_FILE, "r") as f:
                self.original_db = json.load(f)
        with open(EMPLOYERS_FILE, "w") as f:
            json.dump({}, f, indent=2)

    def teardown_method(self):
        with open(EMPLOYERS_FILE, "w") as f:
            json.dump(self.original_db or {}, f, indent=2)

    def test_register_employer_success(self):
        """Test successful employer registration."""
        from auth import register_employer
        
        result = register_employer(
            email="test@company.com",
            password="password123",
            company_name="Test Company"
        )
        
        assert result["success"] is True
        assert "Registration successful" in result["message"]

    def test_register_employer_invalid_email(self):
        """Test registration with invalid email."""
        from auth import register_employer
        
        result = register_employer(
            email="invalid-email",
            password="password123",
            company_name="Test Company"
        )
        
        assert result["success"] is False
        assert "Invalid email" in result["message"]

    def test_register_employer_short_password(self):
        """Test registration with short password."""
        from auth import register_employer
        
        result = register_employer(
            email="test@company.com",
            password="12345",
            company_name="Test Company"
        )
        
        assert result["success"] is False
        assert "at least 6 characters" in result["message"]

    def test_register_employer_missing_company(self):
        """Test registration with missing company name."""
        from auth import register_employer
        
        result = register_employer(
            email="test@company.com",
            password="password123",
            company_name=""
        )
        
        assert result["success"] is False
        assert "required" in result["message"].lower()

    def test_register_employer_duplicate(self):
        """Test duplicate registration."""
        from auth import register_employer
        
        register_employer(
            email="duplicate@company.com",
            password="password123",
            company_name="Company 1"
        )
        
        result = register_employer(
            email="duplicate@company.com",
            password="password456",
            company_name="Company 2"
        )
        
        assert result["success"] is False
        assert "already registered" in result["message"]


class TestEmployerAuthentication:
    """Tests for employer authentication."""

    def setup_method(self):
        self.original_db = {}
        if EMPLOYERS_FILE.exists():
            with open(EMPLOYERS_FILE, "r") as f:
                self.original_db = json.load(f)
        with open(EMPLOYERS_FILE, "w") as f:
            json.dump({}, f, indent=2)

    def teardown_method(self):
        with open(EMPLOYERS_FILE, "w") as f:
            json.dump(self.original_db or {}, f, indent=2)

    def test_authenticate_employer_success(self):
        """Test successful employer authentication."""
        from auth import register_employer, authenticate_employer
        
        register_employer(
            email="auth@test.com",
            password="password123",
            company_name="Auth Company"
        )
        
        result = authenticate_employer("auth@test.com", "password123")
        
        assert result is not None
        assert result["email"] == "auth@test.com"
        assert result["company_name"] == "Auth Company"

    def test_authenticate_employer_wrong_password(self):
        """Test authentication with wrong password."""
        from auth import register_employer, authenticate_employer
        
        register_employer(
            email="wrongpass@test.com",
            password="correctpassword",
            company_name="Company"
        )
        
        result = authenticate_employer("wrongpass@test.com", "wrongpassword")
        
        assert result is None

    def test_authenticate_employer_not_found(self):
        """Test authentication with non-existent employer."""
        from auth import authenticate_employer
        
        result = authenticate_employer("nonexistent@test.com", "anypassword")
        
        assert result is None


class TestEmailValidation:
    """Tests for email validation."""

    def test_valid_email(self):
        """Test valid email addresses."""
        from auth import validate_employer_email
        
        assert validate_employer_email("test@example.com") is True
        assert validate_employer_email("user.name@domain.co.uk") is True
        assert validate_employer_email("user+tag@example.org") is True

    def test_invalid_email(self):
        """Test invalid email addresses."""
        from auth import validate_employer_email
        
        assert validate_employer_email("invalid") is False
        assert validate_employer_email("@nodomain.com") is False
        assert validate_employer_email("noat.com") is False
        assert validate_employer_email("") is False
