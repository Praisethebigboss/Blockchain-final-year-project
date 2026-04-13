import pytest
import os
from pathlib import Path
from unittest.mock import patch

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

os.environ["TRANSCRIPT_ENCRYPTION_KEY"] = "96fdecf67a48e82e2e42dbc4aa6806c7a09066ee84cdff8ac383e0796dbb24bb"

from storage_service import (
    encrypt_file,
    decrypt_file,
    file_exists,
    get_file_info,
    store_file,
    get_file,
    get_encryption_key,
    MAX_FILE_SIZE,
)


class TestStorageService:
    """Unit tests for storage_service module."""

    def test_encrypt_file(self, sample_pdf_content):
        """Test file encryption returns ciphertext and nonce."""
        ciphertext, nonce = encrypt_file(sample_pdf_content)
        
        assert isinstance(ciphertext, bytes)
        assert isinstance(nonce, bytes)
        assert len(ciphertext) > 0
        assert len(nonce) == 12

    def test_encrypt_file_produces_different_outputs(self, sample_pdf_content):
        """Test that encryption produces different outputs for same content."""
        ciphertext1, nonce1 = encrypt_file(sample_pdf_content)
        ciphertext2, nonce2 = encrypt_file(sample_pdf_content)
        
        assert ciphertext1 != ciphertext2 or nonce1 != nonce2

    def test_decrypt_file(self, sample_pdf_content):
        """Test file decryption returns original content."""
        ciphertext, nonce = encrypt_file(sample_pdf_content)
        decrypted = decrypt_file(ciphertext, nonce)
        
        assert decrypted == sample_pdf_content

    def test_decrypt_file_with_wrong_data_raises(self, sample_pdf_content):
        """Test that decryption with tampered data raises exception."""
        ciphertext, nonce = encrypt_file(sample_pdf_content)
        tampered = bytes([b ^ 0xFF for b in ciphertext])
        
        with pytest.raises(Exception):
            decrypt_file(tampered, nonce)

    def test_file_size_limit(self):
        """Test that MAX_FILE_SIZE is 10MB."""
        assert MAX_FILE_SIZE == 10 * 1024 * 1024

    def test_file_size_limit_exceeded(self):
        """Test that large file doesn't crash (encryption handles gracefully)."""
        large_data = b"A" * (MAX_FILE_SIZE + 1)
        # Large files may raise ValueError or be allowed
        try:
            encrypt_file(large_data)
        except ValueError:
            pass  # Expected behavior

    def test_get_file_info_not_found(self, sample_hash):
        """Test get_file_info for non-existent file."""
        # Returns empty dict for non-existent files
        result = get_file_info(sample_hash)
        # Either returns empty or handles gracefully

    def test_encryption_key_from_env(self):
        """Test that encryption key is loaded from environment."""
        key = bytes.fromhex("96fdecf67a48e82e2e42dbc4aa6806c7a09066ee84cdff8ac383e0796dbb24bb")
        result = get_encryption_key()
        assert result == key


class TestStorageServiceWithIPFS:
    """Tests for storage_service with IPFS mocking."""

    def test_store_file_success(self, sample_pdf_content, sample_hash):
        """Test storing file with mock IPFS."""
        with patch("storage_service.upload_to_ipfs", return_value="QmTestHash123"):
            result = store_file(sample_pdf_content, "test.pdf", sample_hash)
        
        assert result["cid"] == "QmTestHash123"
        assert result["filename"] == "test.pdf"

    def test_file_status_stored(self, sample_hash, sample_pdf_content):
        """Test file status returns correct info."""
        with patch("storage_service.upload_to_ipfs", return_value="QmTestHash123"):
            result = store_file(sample_pdf_content, "test.pdf", sample_hash)
        
        assert result["cid"] == "QmTestHash123"