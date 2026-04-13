import pytest
import io
from pathlib import Path
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestAPIEndpoints:
    """Integration tests for API endpoints using FastAPI TestClient."""

    @pytest.fixture
    def client(self):
        """Create TestClient for the FastAPI app."""
        from main import app
        return TestClient(app)

    def test_home_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get("/")
        
        assert response.status_code == 200
        assert "Backend is working" in response.json()["message"]

    def test_hash_endpoint_valid_file(self, client, sample_pdf_content):
        """Test hash endpoint with valid file."""
        response = client.post(
            "/hash",
            files={"file": ("test.pdf", sample_pdf_content, "application/pdf")},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "hash" in data
        assert len(data["hash"]) == 64

    def test_hash_endpoint_no_file(self, client):
        """Test hash endpoint with no file."""
        response = client.post("/hash")
        
        assert response.status_code == 422

    def test_hash_endpoint_empty_file(self, client):
        """Test hash endpoint with empty file."""
        response = client.post(
            "/hash",
            files={"file": ("empty.pdf", b"", "application/pdf")},
        )
        
        assert response.status_code in [400, 422]

    def test_hash_endpoint_pdf_filename(self, client, sample_pdf_content):
        """Test hash endpoint preserves filename."""
        response = client.post(
            "/hash",
            files={"file": ("transcript.pdf", sample_pdf_content, "application/pdf")},
        )
        
        assert response.status_code == 200
        assert response.json()["filename"] == "transcript.pdf"


class TestStoreEndpoint:
    """Tests for /store endpoint."""

    @pytest.fixture
    def client(self):
        """Create TestClient for the FastAPI app."""
        from main import app
        return TestClient(app)

    def test_store_valid_hash(self, client, sample_hash):
        """Test storing valid hash."""
        mock_receipt = MagicMock()
        mock_receipt.transactionHash.hex.return_value = "0xabc123"
        
        with patch("main.store_hash", return_value=mock_receipt):
            response = client.post(
                "/store",
                json={"hash": sample_hash},
            )
        
        assert response.status_code == 200
        assert response.json()["status"] == "stored"

    def test_store_invalid_hash_format(self, client):
        """Test store with invalid hash format."""
        response = client.post(
            "/store",
            json={"hash": "notavalidhash"},
        )
        
        assert response.status_code == 400
        assert "Invalid" in response.json()["detail"]

    def test_store_short_hash(self, client):
        """Test store with too short hash."""
        response = client.post(
            "/store",
            json={"hash": "abc"},
        )
        
        assert response.status_code == 400

    def test_store_long_hash(self, client):
        """Test store with too long hash."""
        response = client.post(
            "/store",
            json={"hash": "a" * 65},
        )
        
        assert response.status_code == 400

    def test_store_empty_hash(self, client):
        """Test store with empty hash."""
        response = client.post(
            "/store",
            json={"hash": ""},
        )
        
        assert response.status_code in [400, 422]

    def test_store_duplicate(self, client, sample_hash):
        """Test storing duplicate hash."""
        from blockchain import DuplicateTranscriptError
        
        with patch("main.store_hash", side_effect=DuplicateTranscriptError("Already issued")):
            response = client.post(
                "/store",
                json={"hash": sample_hash},
            )
        
        assert response.status_code == 409


class TestVerifyEndpoint:
    """Tests for /verify endpoint."""

    @pytest.fixture
    def client(self):
        """Create TestClient for the FastAPI app."""
        from main import app
        return TestClient(app)

    def test_verify_valid_hash_exists(self, client, sample_hash):
        """Test verify for existing hash."""
        with patch("main.verify_hash", return_value=True):
            response = client.get(f"/verify/{sample_hash}")
        
        assert response.status_code == 200
        assert response.json()["exists"] is True

    def test_verify_valid_hash_not_exists(self, client, sample_hash):
        """Test verify for non-existing hash."""
        with patch("main.verify_hash", return_value=False):
            response = client.get(f"/verify/{sample_hash}")
        
        assert response.status_code == 200
        assert response.json()["exists"] is False

    def test_verify_invalid_hash_format(self, client):
        """Test verify with invalid hash."""
        response = client.get("/verify/invalidhash")
        
        assert response.status_code == 400

    def test_verify_connection_error(self, client, sample_hash):
        """Test verify when blockchain unavailable."""
        with patch("main.verify_hash", side_effect=ConnectionError("Not available")):
            response = client.get(f"/verify/{sample_hash}")
        
        assert response.status_code == 503


class TestTranscriptEndpoint:
    """Tests for /transcript endpoint."""

    @pytest.fixture
    def client(self):
        """Create TestClient for the FastAPI app."""
        from main import app
        return TestClient(app)

    def test_get_transcript_success(self, client, sample_hash):
        """Test getting transcript details."""
        with patch("main.get_transcript", return_value={
            "document_hash": sample_hash,
            "issuer": "0xf39Fd6e51aad88F6F4ce6aB8822729c1C9c00003",
            "timestamp": 1234567890,
        }):
            response = client.get(f"/transcript/{sample_hash}")
        
        assert response.status_code == 200
        data = response.json()
        assert "issuer" in data
        assert "timestamp" in data

    def test_get_transcript_not_found(self, client, sample_hash):
        """Test getting non-existent transcript."""
        with patch("main.get_transcript", return_value={"timestamp": 0}):
            response = client.get(f"/transcript/{sample_hash}")
        
        assert response.status_code == 404


class TestFileStatusEndpoint:
    """Tests for /file-status endpoint."""

    @pytest.fixture
    def client(self):
        """Create TestClient for the FastAPI app."""
        from main import app
        return TestClient(app)

    def test_file_status_not_found(self, client, sample_hash):
        """Test file status when not stored."""
        with patch("main.file_exists", return_value=False):
            response = client.get(f"/file-status/{sample_hash}")
        
        assert response.status_code == 200
        assert response.json()["stored"] is False

    def test_file_status_found(self, client, sample_hash):
        """Test file status when stored."""
        with patch("main.file_exists", return_value=True):
            with patch("main.get_file_info", return_value={
                "filename": "test.pdf",
                "size": 1024,
                "cid": "QmTest",
            }):
                response = client.get(f"/file-status/{sample_hash}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["stored"] is True
        assert data["filename"] == "test.pdf"

    def test_file_status_invalid_hash(self, client):
        """Test file status with invalid hash."""
        response = client.get("/file-status/invalid")
        
        assert response.status_code == 400


class TestDownloadEndpoint:
    """Tests for /download endpoint."""

    @pytest.fixture
    def client(self):
        """Create TestClient for the FastAPI app."""
        from main import app
        return TestClient(app)

    def test_download_not_found(self, client, sample_hash):
        """Test download when file not found."""
        with patch("main.get_file", return_value=None):
            response = client.get(f"/download/{sample_hash}")
        
        assert response.status_code == 404

    def test_download_success(self, client, sample_hash):
        """Test successful file download."""
        with patch("main.get_file", return_value={
            "data": b"test content",
            "filename": "test.pdf",
            "size": 12,
        }):
            response = client.get(f"/download/{sample_hash}")
        
        assert response.status_code == 200

    def test_download_invalid_hash(self, client):
        """Test download with invalid hash."""
        response = client.get("/download/invalid")
        
        assert response.status_code == 400


class TestPaginationEndpoint:
    """Tests for /transcripts endpoint."""

    @pytest.fixture
    def client(self):
        """Create TestClient for the FastAPI app."""
        from main import app
        return TestClient(app)

    def test_list_transcripts_default(self, client):
        """Test listing transcripts with default pagination."""
        with patch("main.get_total_count", return_value=0):
            with patch("main.list_transcripts", return_value=[]):
                response = client.get("/transcripts")
        
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "transcripts" in data

    def test_list_transcripts_custom_pagination(self, client):
        """Test listing transcripts with custom pagination."""
        with patch("main.get_total_count", return_value=10):
            with patch("main.list_transcripts", return_value=[]):
                response = client.get("/transcripts?offset=5&limit=10")
        
        assert response.status_code == 200

    def test_list_transcripts_invalid_offset(self, client):
        """Test with negative offset."""
        response = client.get("/transcripts?offset=-1")
        
        assert response.status_code == 400

    def test_list_transcripts_invalid_limit_zero(self, client):
        """Test with zero limit."""
        response = client.get("/transcripts?limit=0")
        
        assert response.status_code == 400

    def test_list_transcripts_limit_too_large(self, client):
        """Test with limit exceeding max."""
        response = client.get("/transcripts?limit=101")
        
        assert response.status_code == 400


class TestStoreFileEndpoint:
    """Tests for /store-file endpoint."""

    @pytest.fixture
    def client(self):
        """Create TestClient for the FastAPI app."""
        from main import app
        return TestClient(app)

    def test_store_file_success(self, client, sample_pdf_content):
        """Test storing file."""
        with patch("main.generate_file_hash", return_value="a" * 64):
            with patch("main.store_file", return_value={
                "cid": "QmTest",
                "filename": "test.pdf",
            }):
                response = client.post(
                    "/store-file",
                    files={"file": ("test.pdf", sample_pdf_content, "application/pdf")},
                )
        
        assert response.status_code == 200
        assert "cid" in response.json()

    def test_store_file_empty(self, client):
        """Test storing empty file."""
        response = client.post(
            "/store-file",
            files={"file": ("empty.pdf", b"", "application/pdf")},
        )
        
        assert response.status_code in [400, 422]


def test_conftest_loaded():
    """Verify conftest fixtures are loaded."""
    from test.conftest import clean_test_db, sample_pdf_content, sample_hash
    assert clean_test_db is not None
    assert sample_pdf_content is not None
    assert sample_hash is not None


class TestBatchStoreEndpoint:
    """Tests for /batch-store endpoint."""

    @pytest.fixture
    def client(self):
        """Create TestClient for the FastAPI app."""
        from main import app
        return TestClient(app)

    def test_batch_store_no_files(self, client):
        """Test batch store with no files."""
        response = client.post("/batch-store")
        
        assert response.status_code in [400, 422]

    def test_batch_store_too_many_files(self, client, sample_pdf_content):
        """Test batch store with too many files."""
        files = [
            ("files", (f"file{i}.pdf", sample_pdf_content, "application/pdf"))
            for i in range(21)
        ]
        response = client.post("/batch-store", files=files)
        
        assert response.status_code == 400

    def test_batch_store_single_file(self, client, sample_pdf_content):
        """Test batch store with one file."""
        mock_receipt = MagicMock()
        mock_receipt.transactionHash.hex.return_value = "0xabc123"
        
        with patch("main.generate_file_hash", return_value="a" * 64):
            with patch("main.store_hash", return_value=mock_receipt):
                response = client.post(
                    "/batch-store",
                    files={"files": ("test.pdf", sample_pdf_content, "application/pdf")},
                )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["results"][0]["status"] == "stored"

    def test_batch_store_multiple_files(self, client, sample_pdf_content):
        """Test batch store with multiple files."""
        mock_receipt = MagicMock()
        mock_receipt.transactionHash.hex.return_value = "0xabc123"
        
        files = [
            ("files", (f"file{i}.pdf", sample_pdf_content, "application/pdf"))
            for i in range(3)
        ]
        
        with patch("main.generate_file_hash", return_value="a" * 64):
            with patch("main.store_hash", return_value=mock_receipt):
                response = client.post("/batch-store", files=files)
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3

    def test_batch_store_duplicate_handling(self, client, sample_pdf_content):
        """Test batch store handles duplicates."""
        from blockchain import DuplicateTranscriptError
        
        with patch("main.generate_file_hash", return_value="a" * 64):
            with patch("main.store_hash", side_effect=DuplicateTranscriptError("Already issued")):
                response = client.post(
                    "/batch-store",
                    files={"files": ("test.pdf", sample_pdf_content, "application/pdf")},
                )
        
        assert response.status_code == 200
        data = response.json()
        assert data["results"][0]["status"] == "duplicate"