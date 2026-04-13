import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend_client import BackendClient, BackendError, DuplicateError
import requests


class TestBackendClient:
    """Tests for BackendClient."""

    def test_client_initialization(self):
        """Test client is initialized with default values."""
        client = BackendClient(
            base_url="http://localhost:8000",
            frontend_url="http://localhost:8501",
        )
        assert client.base_url == "http://localhost:8000"
        assert client.frontend_url == "http://localhost:8501"

    def test_client_custom_urls(self):
        """Test client with custom URLs."""
        client = BackendClient(
            base_url="http://custom:9000",
            frontend_url="http://custom:9001",
        )
        assert client.base_url == "http://custom:9000"
        assert client.frontend_url == "http://custom:9001"


class TestBackendClientMethods:
    """Tests for BackendClient methods."""

    def test_store_hash_success(self):
        """Test store_hash success."""
        client = BackendClient()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "stored", "tx": "0xabc"}
        
        with patch("requests.post", return_value=mock_response):
            result = client.store_hash("a" * 64)
        
        assert result["status"] == "stored"

    def test_store_hash_duplicate(self):
        """Test store_hash duplicate handling."""
        client = BackendClient()
        mock_response = MagicMock()
        mock_response.status_code = 409
        mock_response.json.return_value = {"detail": "Already issued"}
        
        with patch("requests.post", return_value=mock_response):
            with pytest.raises(DuplicateError):
                client.store_hash("a" * 64)

    def test_verify_hash_success(self):
        """Test verify_hash success."""
        client = BackendClient()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"hash": "a" * 64, "exists": True}
        
        with patch("requests.get", return_value=mock_response):
            result = client.verify_hash("a" * 64)
        
        assert result["exists"] is True

    def test_verify_hash_not_found(self):
        """Test verify_hash when not found."""
        client = BackendClient()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"hash": "a" * 64, "exists": False}
        
        with patch("requests.get", return_value=mock_response):
            result = client.verify_hash("a" * 64)
        
        assert result["exists"] is False

    def test_verify_hash_timeout(self):
        """Test verify_hash timeout."""
        client = BackendClient()
        
        with patch("requests.get", side_effect=requests.exceptions.Timeout()):
            with pytest.raises(BackendError) as exc:
                client.verify_hash("a" * 64)
        assert exc.value.status_code == 503

    def test_get_transcript_success(self):
        """Test get_transcript success."""
        client = BackendClient()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "hash": "a" * 64,
            "issuer": "0x123",
            "timestamp": 1234567890,
        }
        
        with patch("requests.get", return_value=mock_response):
            result = client.get_transcript("a" * 64)
        
        assert result["issuer"] == "0x123"

    def test_get_transcript_not_found(self):
        """Test get_transcript not found."""
        client = BackendClient()
        mock_response = MagicMock()
        mock_response.status_code = 404
        
        with patch("requests.get", return_value=mock_response):
            result = client.get_transcript("a" * 64)
        
        assert result is None

    def test_store_file_success(self):
        """Test store_file success."""
        client = BackendClient()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"cid": "QmTest", "hash": "a" * 64}
        
        with patch("requests.post", return_value=mock_response):
            result = client.store_file(b"test content", "test.pdf")
        
        assert result["cid"] == "QmTest"

    def test_store_file_timeout(self):
        """Test store_file timeout."""
        client = BackendClient()
        
        with patch("requests.post", side_effect=requests.exceptions.Timeout()):
            with pytest.raises(BackendError) as exc:
                client.store_file(b"test", "test.pdf")
        assert exc.value.status_code == 503

    def test_get_file_status_success(self):
        """Test get_file_status success."""
        client = BackendClient()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"stored": True, "filename": "test.pdf"}
        
        with patch("requests.get", return_value=mock_response):
            result = client.get_file_status("a" * 64)
        
        assert result["stored"] is True

    def test_get_file_status_not_stored(self):
        """Test get_file_status when not stored."""
        client = BackendClient()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"stored": False}
        
        with patch("requests.get", return_value=mock_response):
            result = client.get_file_status("a" * 64)
        
        assert result["stored"] is False

    def test_get_verification_url(self):
        """Test verification URL generation."""
        client = BackendClient()
        url = client.get_verification_url("abc123")
        
        assert "3_Student.py" in url
        assert "verify=abc123" in url

    def test_get_download_url(self):
        """Test download URL generation."""
        client = BackendClient()
        url = client.get_download_url("abc123")
        
        assert "download" in url
        assert "abc123" in url


class TestBackendErrorException:
    """Tests for BackendError exception."""

    def test_error_creation(self):
        """Test BackendError can be created."""
        error = BackendError("Test error", 500)
        assert error.message == "Test error"
        assert error.status_code == 500

    def test_error_default_status(self):
        """Test BackendError default status."""
        error = BackendError("Test error")
        assert error.status_code is None


class TestDuplicateErrorException:
    """Tests for DuplicateError exception."""

    def test_duplicate_error_creation(self):
        """Test DuplicateError can be created."""
        error = DuplicateError("Already issued", 409)
        assert error.message == "Already issued"
        assert error.status_code == 409


def test_backend_client_import():
    """Test that backend_client can be imported."""
    from backend_client import BackendClient
    assert BackendClient is not None


def test_error_classes_import():
    """Test that error classes can be imported."""
    from backend_client import BackendError, DuplicateError
    assert BackendError is not None
    assert DuplicateError is not None


def test_list_transcripts():
    """Test list_transcripts method."""
    client = BackendClient()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "total": 2,
        "offset": 0,
        "limit": 10,
        "transcripts": [
            {"hash": "a" * 64, "issuer": "0x123", "timestamp": 1234567890},
            {"hash": "b" * 64, "issuer": "0x456", "timestamp": 1234567891},
        ],
    }
    
    with patch("requests.get", return_value=mock_response):
        result = client.list_transcripts(offset=0, limit=10)
    
    assert result["total"] == 2
    assert len(result["transcripts"]) == 2