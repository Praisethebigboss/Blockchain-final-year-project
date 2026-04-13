import pytest
import os
import json
from pathlib import Path
from unittest.mock import MagicMock, patch, PropertyMock

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

os.environ["ETHEREUM_NETWORK"] = "localhost"


class TestBlockchainService:
    """Unit tests for blockchain module with mocked web3."""

    @pytest.fixture
    def mock_web3_instance(self):
        """Create a mocked web3 instance."""
        mock_w3 = MagicMock()
        mock_contract = MagicMock()
        mock_account = "0xf39Fd6e51aad88F6F4ce6aB8822729c1C9c00003"
        
        mock_contract.functions.issueTranscript.return_value.transact.return_value = MagicMock(
            transactionHash=b"\x01"
        )
        mock_contract.functions.verifyTranscript.return_value.call.return_value = True
        mock_contract.functions.transcripts.return_value.call.return_value = (
            "a" * 64,
            mock_account,
            1234567890,
        )
        
        mock_w3.eth.contract.return_value = mock_contract
        mock_w3.eth.accounts = [mock_account]
        mock_w3.eth.wait_for_transaction_receipt.return_value = MagicMock(
            transactionHash=b"\x01",
            blockNumber=1,
        )
        
        return mock_w3

    def test_contract_address_from_env(self):
        """Test that contract address is loaded from environment."""
        from blockchain import contract_address
        
        assert contract_address is not None
        assert contract_address.startswith("0x")

    def test_contract_address_from_config_file(self):
        """Test that contract address can be loaded from config file."""
        config_path = Path(__file__).parent.parent / "contract-config.json"
        test_address = "0x1234567890123456789012345678901234567890"
        
        with open(config_path, "w") as f:
            json.dump({"contract_address": test_address}, f)
        
        try:
            from blockchain import _get_contract_address_from_file
            result = _get_contract_address_from_file()
            assert result == test_address
        finally:
            if config_path.exists():
                config_path.unlink()

    def test_network_configs(self):
        """Test that network configurations are defined."""
        from blockchain import NETWORK_CONFIGS
        
        assert "localhost" in NETWORK_CONFIGS
        assert "sepolia" in NETWORK_CONFIGS
        assert "mainnet" in NETWORK_CONFIGS

    def test_rpc_url_localhost(self):
        """Test localhost RPC URL."""
        from blockchain import _get_rpc_url
        
        url = _get_rpc_url("localhost")
        assert "127.0.0.1" in url

    def test_rpc_url_sepolia(self):
        """Test sepolia RPC URL."""
        from blockchain import _get_rpc_url
        
        url = _get_rpc_url("sepolia")
        assert "sepolia" in url

    def test_rpc_url_unknown_network(self):
        """Test unknown network uses provided URL directly."""
        from blockchain import _get_rpc_url
        
        custom_url = "http://custom:8545"
        url = _get_rpc_url(custom_url)
        assert url == custom_url


class TestBlockchainFunctionsWithMock:
    """Tests for blockchain functions with mocked web3."""

    @pytest.fixture
    def setup_mock_blockchain(self):
        """Setup mock for blockchain module."""
        mock_w3 = MagicMock()
        mock_contract = MagicMock()
        
        mock_contract.functions.verifyTranscript.return_value.call.return_value = True
        mock_contract.functions.transcripts.return_value.call.return_value = (
            "a" * 64,
            "0xf39Fd6e51aad88F6F4ce6aB8822729c1C9c00003",
            1234567890,
        )
        
        mock_w3.eth.contract.return_value = mock_contract
        mock_w3.is_connected = lambda: True
        
        with patch("blockchain.w3", mock_w3):
            with patch("blockchain._get_contract", return_value=mock_contract):
                yield mock_w3, mock_contract

    def test_verify_hash_success(self, setup_mock_blockchain):
        """Test verify_hash returns True for existing hash."""
        from blockchain import verify_hash
        
        result = verify_hash("a" * 64)
        assert result is True

    def test_get_transcript_success(self, setup_mock_blockchain):
        """Test get_transcript returns transcript data."""
        from blockchain import get_transcript
        
        result = get_transcript("a" * 64)
        
        assert result["document_hash"] == "a" * 64
        assert result["issuer"] == "0xf39Fd6e51aad88F6F4ce6aB8822729c1C9c00003"
        assert result["timestamp"] == 1234567890


class TestBlockchainErrors:
    """Tests for blockchain error handling."""

    def test_verify_hash_connection_error(self):
        """Test verify_hash raises ConnectionError on failure."""
        from blockchain import verify_hash
        
        with patch("blockchain._get_contract") as mock_contract:
            mock_contract.side_effect = Exception("Connection refused")
            
            with pytest.raises(ConnectionError):
                verify_hash("a" * 64)

    def test_get_transcript_connection_error(self):
        """Test get_transcript raises ConnectionError on failure."""
        from blockchain import get_transcript
        
        with patch("blockchain._get_contract") as mock_contract:
            mock_contract.side_effect = Exception("Connection refused")
            
            with pytest.raises(ConnectionError):
                get_transcript("a" * 64)


class TestDuplicateTranscriptError:
    """Tests for DuplicateTranscriptError exception."""

    def test_duplicate_error_creation(self):
        """Test DuplicateTranscriptError can be created."""
        from blockchain import DuplicateTranscriptError
        
        error = DuplicateTranscriptError("Already issued")
        assert str(error) == "Already issued"

    def test_duplicate_error_raising(self):
        """Test DuplicateTranscriptError can be raised and caught."""
        from blockchain import DuplicateTranscriptError
        
        with pytest.raises(DuplicateTranscriptError):
            raise DuplicateTranscriptError("Test error")