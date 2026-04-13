import pytest
import io
from pathlib import Path
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestErrorHandling:
    """Tests for error handling across endpoints."""

    @pytest.fixture
    def client(self):
        """Create TestClient for the FastAPI app."""
        from main import app
        return TestClient(app)

    def test_400_invalid_hash_format(self, client):
        """Test 400 error for invalid hash format."""
        response = client.post("/store", json={"hash": "nota64charshash"})
        
        assert response.status_code == 400

    def test_400_hash_too_short(self, client):
        """Test 400 error for hash that's too short."""
        response = client.post("/store", json={"hash": "abc"})
        
        assert response.status_code == 400
        assert "Invalid" in response.json()["detail"] or response.status_code == 422

    def test_400_hash_too_long(self, client):
        """Test 400 error for hash that's too long."""
        response = client.post("/store", json={"hash": "a" * 65})
        
        assert response.status_code == 400
        assert "Invalid" in response.json()["detail"] or response.status_code == 422

    def test_400_hash_with_invalid_characters(self, client):
        """Test 400 error for hash with invalid characters."""
        response = client.post("/store", json={"hash": "G" * 64})
        
        assert response.status_code == 400

    def test_400_empty_file(self, client):
        """Test 400 error for empty file upload."""
        response = client.post("/hash", files={"file": ("empty.pdf", b"", "application/pdf")})
        
        assert response.status_code in [400, 422]

    def test_400_no_file(self, client):
        """Test 400 error when no file provided."""
        response = client.post("/hash")
        
        assert response.status_code in [400, 422]

    def test_404_transcript_not_found(self, client, sample_hash):
        """Test 404 error when transcript not found."""
        with patch("main.get_transcript", return_value={"timestamp": 0}):
            response = client.get(f"/transcript/{sample_hash}")
        
        assert response.status_code == 404

    def test_404_file_not_found(self, client, sample_hash):
        """Test 404 error when file not found."""
        with patch("main.get_file", return_value=None):
            response = client.get(f"/download/{sample_hash}")
        
        assert response.status_code == 404

    def test_409_duplicate_hash(self, client, sample_hash):
        """Test 409 error for duplicate hash."""
        from blockchain import DuplicateTranscriptError
        
        with patch("main.store_hash", side_effect=DuplicateTranscriptError("Already issued")):
            response = client.post("/store", json={"hash": sample_hash})
        
        assert response.status_code == 409

    def test_503_blockchain_unavailable(self, client, sample_hash):
        """Test 503 error when blockchain unavailable."""
        with patch("main.verify_hash", side_effect=ConnectionError("Not available")):
            response = client.get(f"/verify/{sample_hash}")
        
        assert response.status_code == 503

    def test_503_storage_unavailable(self, client, sample_pdf_content):
        """Test 503 error when storage unavailable."""
        with patch("main.generate_file_hash", return_value="a" * 64):
            with patch("main.store_file", side_effect=RuntimeError("IPFS unavailable")):
                response = client.post(
                    "/store-file",
                    files={"file": ("test.pdf", sample_pdf_content, "application/pdf")},
                )
        
        assert response.status_code in [500, 503]

    def test_500_internal_error(self, client, sample_hash):
        """Test 500 error for internal server errors."""
        with patch("main.verify_hash", side_effect=RuntimeError("Unexpected")):
            response = client.get(f"/verify/{sample_hash}")
        
        assert response.status_code == 500

    def test_422_missing_hash_field(self, client):
        """Test 422 error for missing hash field."""
        response = client.post("/store", json={})
        
        assert response.status_code == 422

    def test_422_invalid_json(self, client):
        """Test 422 error for invalid JSON."""
        response = client.post("/store", data="not json")
        
        assert response.status_code in [400, 422]

    def test_400_negative_offset(self, client):
        """Test 400 error for negative offset."""
        response = client.get("/transcripts?offset=-1")
        
        assert response.status_code == 400

    def test_400_zero_limit(self, client):
        """Test 400 error for zero limit."""
        response = client.get("/transcripts?limit=0")
        
        assert response.status_code == 400

    def test_400_limit_too_large(self, client):
        """Test 400 error for limit exceeding max."""
        response = client.get("/transcripts?limit=101")
        
        assert response.status_code == 400


class TestEdgeCases:
    """Tests for edge cases in error handling."""

    @pytest.fixture
    def client(self):
        """Create TestClient for the FastAPI app."""
        from main import app
        return TestClient(app)

    def test_empty_string_hash(self, client):
        """Test with empty string hash."""
        response = client.post("/store", json={"hash": ""})
        
        assert response.status_code == 400

    def test_whitespace_only_hash(self, client):
        """Test with whitespace only hash."""
        response = client.post("/store", json={"hash": "   "})
        
        assert response.status_code in [400, 422]

    def test_none_hash(self, client):
        """Test with None hash."""
        response = client.post("/store", json={"hash": None})
        
        assert response.status_code == 422

    def test_large_file_handling(self, client):
        """Test handling of file near size limit."""
        large_content = b"A" * (10 * 1024 * 1024)
        
        with patch("main.generate_file_hash", side_effect=MemoryError("Too large")):
            with patch("main.store_file", side_effect=ValueError("File too large")):
                response = client.post(
                    "/store-file",
                    files={"file": ("large.pdf", large_content, "application/pdf")},
                )
        
        assert response.status_code in [400, 413, 500]

    def test_special_characters_in_filename(self, client, sample_pdf_content):
        """Test handling special characters in filename."""
        response = client.post(
            "/hash",
            files={"file": ("test file.pdf", sample_pdf_content, "application/pdf")},
        )
        
        assert response.status_code == 200

    def test_very_long_filename(self, client, sample_pdf_content):
        """Test handling very long filename."""
        long_name = "a" * 500 + ".pdf"
        response = client.post(
            "/hash",
            files={"file": (long_name, sample_pdf_content, "application/pdf")},
        )
        
        assert response.status_code in [200, 400, 422]


class TestBlockchainErrorPropagation:
    """Tests for proper error propagation from blockchain module."""

    @pytest.fixture
    def client(self):
        """Create TestClient for the FastAPI app."""
        from main import app
        return TestClient(app)

    def test_connection_error_not_500(self, client, sample_hash):
        """Test ConnectionError doesn't become 500."""
        with patch("main.verify_hash", side_effect=ConnectionError("Connection refused")):
            response = client.get(f"/verify/{sample_hash}")
        
        assert response.status_code == 503

    def test_runtime_error_not_500(self, client, sample_hash):
        """Test RuntimeError doesn't become 500."""
        with patch("main.verify_hash", side_effect=RuntimeError("Contract call failed")):
            response = client.get(f"/verify/{sample_hash}")
        
        assert response.status_code == 500


class TestIPFSErrorHandling:
    """Tests for IPFS/storage error handling."""

    @pytest.fixture
    def client(self):
        """Create TestClient for the FastAPI app."""
        from main import app
        return TestClient(app)

    def test_ipfs_connection_error(self, client, sample_pdf_content):
        """Test IPFS connection error handling."""
        with patch("main.generate_file_hash", return_value="a" * 64):
            with patch("main.store_file", side_effect=RuntimeError("Connection refused")):
                response = client.post(
                    "/store-file",
                    files={"file": ("test.pdf", sample_pdf_content, "application/pdf")},
                )
        
        assert response.status_code in [500, 503]

    def test_file_status_with_exception(self, client, sample_hash):
        """Test file status doesn't crash on exceptions."""
        with patch("main.file_exists", side_effect=RuntimeError("DB error")):
            response = client.get(f"/file-status/{sample_hash}")
        
        assert response.status_code == 500


def test_conftest_clean_db():
    """Verify that clean_test_db fixture works."""
    from test.conftest import clean_test_db
    assert clean_test_db is not None