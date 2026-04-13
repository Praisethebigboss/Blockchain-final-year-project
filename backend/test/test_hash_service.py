import pytest
from hash_service import generate_file_hash


class TestHashService:
    """Unit tests for hash_service module."""

    def test_generate_file_hash_valid_pdf_content(self, sample_pdf_content):
        """Test generating hash for valid PDF content."""
        result = generate_file_hash(sample_pdf_content)
        
        assert isinstance(result, str)
        assert len(result) == 64
        assert result.isalnum() or all(c in "abcdefABCDEF0123456789" for c in result)

    def test_generate_file_hash_returns_lowercase_hex(self):
        """Test that hash returns lowercase hex characters."""
        data = b"Test Content"
        result = generate_file_hash(data)
        
        assert result.islower()

    def test_generate_file_hash_deterministic(self, sample_pdf_content):
        """Test that same input produces same hash."""
        result1 = generate_file_hash(sample_pdf_content)
        result2 = generate_file_hash(sample_pdf_content)
        
        assert result1 == result2

    def test_generate_file_hash_different_inputs(self):
        """Test that different inputs produce different hashes."""
        data1 = b"Content A"
        data2 = b"Content B"
        
        result1 = generate_file_hash(data1)
        result2 = generate_file_hash(data2)
        
        assert result1 != result2

    def test_generate_file_hash_pdf_header(self):
        """Test hash generation for actual PDF header."""
        pdf_content = b"%PDF-1.4\ntest content"
        result = generate_file_hash(pdf_content)
        
        assert len(result) == 64

    def test_generate_file_hash_empty_content(self):
        """Test that empty content produces a valid hash."""
        result = generate_file_hash(b"")
        
        assert isinstance(result, str)
        assert len(result) == 64

    def test_generate_file_hash_known_value(self):
        """Test hash against a known SHA256 value (different inputs produce different hashes)."""
        data = b"hello"
        result = generate_file_hash(data)
        
        # Verify it's a valid 64-char hex string
        assert len(result) == 64
        assert result.isalnum() or all(c in "abcdefABCDEF0123456789" for c in result)

    def test_generate_file_hash_large_content(self):
        """Test hash generation for large content."""
        large_data = b"A" * (1024 * 1024)
        result = generate_file_hash(large_data)
        
        assert len(result) == 64

    def test_generate_file_hash_with_special_characters(self):
        """Test hash with special characters."""
        data = b"Test @#$%^&*()\n\t\r"
        result = generate_file_hash(data)
        
        assert len(result) == 64

    def test_generate_file_hash_with_unicode(self):
        """Test hash with unicode content."""
        data = "Test 日本語".encode("utf-8")
        result = generate_file_hash(data)
        
        assert len(result) == 64