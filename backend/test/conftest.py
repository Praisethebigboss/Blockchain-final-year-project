import os
import sys
import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent))

os.environ["TRANSCRIPT_ENCRYPTION_KEY"] = "96fdecf67a48e82e2e42dbc4aa6806c7a09066ee84cdff8ac383e0796dbb24bb"
os.environ["ETHEREUM_NETWORK"] = "localhost"

TEST_DB_PATH = Path(__file__).parent.parent / "storage_db.json"


@pytest.fixture(autouse=True)
def clean_test_db():
    """Clean up test database before and after each test."""
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()
    yield
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()


@pytest.fixture
def mock_web3():
    """Create a mocked web3 instance."""
    with patch("blockchain._init_web3") as mock:
        mock_w3 = MagicMock()
        mock_w3.eth.contract.return_value = MagicMock()
        mock_w3.eth.accounts = ["0xf39Fd6e51aad88F6F4ce6aB8822729c1C9c00003"]
        mock.return_value = mock_w3
        yield mock_w3


@pytest.fixture
def sample_pdf_content():
    """Generate sample PDF content for testing."""
    return b"%PDF-1.4\ntest content for transcript"


@pytest.fixture
def sample_hash():
    """Return a valid SHA256 hash for testing."""
    return "a" * 64


@pytest.fixture
def invalid_hashes():
    """Return invalid hash formats for validation testing."""
    return [
        "notenough",
        "a" * 63,
        "a" * 65,
        "ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ",
        "",
        "     ",
    ]


@pytest.fixture
def mock_ipfs():
    """Create a mocked IPFS client."""
    with patch("storage_service.ipfshttpclient") as mock:
        client = MagicMock()
        client.add_bytes.return_value = "QmTestHash"
        client.cat.return_value = b"decrypted content"
        mock.connect.return_value.__enter__ = MagicMock(return_value=client)
        mock.connect.return_value.__exit__ = MagicMock(return_value=False)
        yield client