import os
import json
import time
from pathlib import Path
from cryptography.hazmat.primitives.ciphers.aead import AES256GCM

STORAGE_DB = Path(__file__).parent / "storage_db.json"
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB limit


def _load_db():
    if not STORAGE_DB.exists():
        return {}
    with open(STORAGE_DB) as f:
        return json.load(f)


def _save_db(db):
    with open(STORAGE_DB, "w") as f:
        json.dump(db, f, indent=2)


def get_encryption_key():
    key = os.environ.get("TRANSCRIPT_ENCRYPTION_KEY")
    if not key:
        raise RuntimeError("TRANSCRIPT_ENCRYPTION_KEY not set. Run: python -c \"import secrets; print('TRANSCRIPT_ENCRYPTION_KEY=' + secrets.token_hex(32))\"")
    return bytes.fromhex(key)


def encrypt_file(data: bytes) -> tuple[bytes, bytes]:
    key = get_encryption_key()
    aesgcm = AES256GCM(key)
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, data, None)
    return ciphertext, nonce


def decrypt_file(ciphertext: bytes, nonce: bytes) -> bytes:
    key = get_encryption_key()
    aesgcm = AES256GCM(key)
    return aesgcm.decrypt(nonce, ciphertext, None)


def upload_to_ipfs(data: bytes) -> str:
    import ipfshttpclient
    with ipfshttpclient.connect("/ip4/127.0.0.1/tcp/5001") as client:
        res = client.add_bytes(data)
        return res["Hash"]


def download_from_ipfs(cid: str) -> bytes:
    import ipfshttpclient
    with ipfshttpclient.connect("/ip4/127.0.0.1/tcp/5001") as client:
        return client.cat(cid)


def store_file(file_bytes: bytes, filename: str, file_hash: str) -> dict:
    if len(file_bytes) > MAX_FILE_SIZE:
        raise ValueError(f"File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB")
    
    encrypted_data, nonce = encrypt_file(file_bytes)
    cid = upload_to_ipfs(encrypted_data)
    
    db = _load_db()
    db[file_hash] = {
        "cid": cid,
        "filename": filename,
        "nonce": nonce.hex(),
        "timestamp": int(time.time()),
        "size": len(file_bytes),
    }
    _save_db(db)
    
    return {"cid": cid, "filename": filename}


def get_file(file_hash: str) -> dict | None:
    db = _load_db()
    if file_hash not in db:
        return None
    
    entry = db[file_hash]
    encrypted_data = download_from_ipfs(entry["cid"])
    plaintext = decrypt_file(encrypted_data, bytes.fromhex(entry["nonce"]))
    
    return {
        "filename": entry["filename"],
        "data": plaintext,
        "size": entry.get("size", len(plaintext)),
    }


def file_exists(file_hash: str) -> bool:
    return file_hash in _load_db()


def get_file_info(file_hash: str) -> dict | None:
    db = _load_db()
    if file_hash not in db:
        return None
    entry = db[file_hash]
    return {
        "filename": entry["filename"],
        "size": entry.get("size", 0),
        "timestamp": entry.get("timestamp", 0),
        "cid": entry["cid"],
    }
