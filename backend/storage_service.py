import os
import json
import time
from pathlib import Path
from cryptography.hazmat.primitives.ciphers.aead import AESGCM as AES256GCM

STORAGE_DB = Path(__file__).parent / "storage_db.json"
LOCAL_FILES_DIR = Path(__file__).parent / "files"
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB limit

LOCAL_FILES_DIR.mkdir(exist_ok=True)


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


def _get_ipfs_connect_string():
    host = os.environ.get("IPFS_HOST", "127.0.0.1")
    port = os.environ.get("IPFS_PORT", "5001")
    return f"/ip4/{host}/tcp/{port}"


def upload_to_ipfs(data: bytes) -> str:
    import ipfshttpclient
    import ipfshttpclient.client as client_mod
    orig = client_mod.assert_version
    def patched(v, mn=client_mod.VERSION_MINIMUM, mx="0.41.0", bl=client_mod.VERSION_BLACKLIST):
        return orig(v, mn, "0.41.0", bl)
    client_mod.assert_version = patched
    with ipfshttpclient.connect(_get_ipfs_connect_string()) as client:
        cid = client.add_bytes(data)
        return cid


def download_from_ipfs(cid: str) -> bytes:
    import ipfshttpclient
    import ipfshttpclient.client as client_mod
    orig = client_mod.assert_version
    def patched(v, mn=client_mod.VERSION_MINIMUM, mx="0.41.0", bl=client_mod.VERSION_BLACKLIST):
        return orig(v, mn, "0.41.0", bl)
    client_mod.assert_version = patched
    with ipfshttpclient.connect(_get_ipfs_connect_string()) as client:
        return client.cat(cid)


def store_file(file_bytes: bytes, filename: str, file_hash: str) -> dict:
    if len(file_bytes) > MAX_FILE_SIZE:
        raise ValueError(f"File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB")
    
    encrypted_data, nonce = encrypt_file(file_bytes)
    
    try:
        cid = upload_to_ipfs(encrypted_data)
        storage_type = "ipfs"
    except Exception:
        local_path = LOCAL_FILES_DIR / f"{file_hash}.enc"
        with open(local_path, "wb") as f:
            f.write(encrypted_data)
        cid = f"local:{local_path.name}"
        storage_type = "local"
    
    db = _load_db()
    db[file_hash] = {
        "cid": cid,
        "filename": filename,
        "nonce": nonce.hex(),
        "timestamp": int(time.time()),
        "size": len(file_bytes),
        "storage_type": storage_type,
    }
    _save_db(db)
    
    return {"cid": cid, "filename": filename, "storage_type": storage_type}


def get_file(file_hash: str) -> dict | None:
    db = _load_db()
    if file_hash not in db:
        return None
    
    entry = db[file_hash]
    storage_type = entry.get("storage_type", "ipfs")
    
    if storage_type == "local" and entry["cid"].startswith("local:"):
        local_path = LOCAL_FILES_DIR / entry["cid"].replace("local:", "")
        with open(local_path, "rb") as f:
            encrypted_data = f.read()
    else:
        try:
            encrypted_data = download_from_ipfs(entry["cid"])
        except Exception:
            return None
    
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


# ============== STUDENT TOKEN STORAGE ==============

TOKENS_DB = Path(__file__).parent / "tokens_db.json"
TOKEN_EXPIRY_SECONDS = 24 * 60 * 60  # 24 hours


def _load_tokens_db():
    if not TOKENS_DB.exists():
        return {}
    with open(TOKENS_DB) as f:
        return json.load(f)


def _save_tokens_db(db):
    with open(TOKENS_DB, "w") as f:
        json.dump(db, f, indent=2)


def store_student_token(file_hash: str, token: str, student_email: str = "") -> dict:
    """Store a student access token for a transcript."""
    db = _load_tokens_db()
    created_at = int(time.time())
    expires_at = created_at + TOKEN_EXPIRY_SECONDS
    
    db[file_hash] = {
        "token": token,
        "student_email": student_email,
        "created_at": created_at,
        "expires_at": expires_at,
        "used": False,
    }
    _save_tokens_db(db)
    
    return {
        "hash": file_hash,
        "token": token,
        "expires_at": expires_at,
    }


def get_token(hash_value: str) -> dict | None:
    """Get token info for a hash."""
    db = _load_tokens_db()
    return db.get(hash_value)


def invalidate_token(hash_value: str) -> bool:
    """Mark a token as used (one-time download)."""
    db = _load_tokens_db()
    if hash_value not in db:
        return False
    db[hash_value]["used"] = True
    _save_tokens_db(db)
    return True


def validate_student_token(hash_value: str, token: str) -> dict:
    """
    Validate a student token.
    Returns dict with 'valid' (bool) and 'error' (str) keys.
    """
    db = _load_tokens_db()
    
    if hash_value not in db:
        return {"valid": False, "error": "Token not found"}
    
    entry = db[hash_value]
    
    if entry["token"] != token:
        return {"valid": False, "error": "Invalid token"}
    
    if entry["used"]:
        return {"valid": False, "error": "Link already used"}
    
    current_time = int(time.time())
    if current_time > entry["expires_at"]:
        return {"valid": False, "error": "Link expired"}
    
    return {"valid": True, "error": None}


def get_transcripts_by_email(student_email: str) -> list:
    """
    Get all transcript tokens for a given student email.
    Returns list of dicts with hash, email, created_at, expires_at, used.
    """
    db = _load_tokens_db()
    transcripts = []
    for hash_value, entry in db.items():
        if entry.get("student_email", "").lower() == student_email.lower():
            transcripts.append({
                "hash": hash_value,
                "student_email": entry.get("student_email", ""),
                "created_at": entry.get("created_at", 0),
                "expires_at": entry.get("expires_at", 0),
                "used": entry.get("used", False),
            })
    return transcripts
