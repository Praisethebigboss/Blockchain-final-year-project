import os
import requests
from dotenv import load_dotenv

load_dotenv()


class BackendError(Exception):
    def __init__(self, message: str, status_code: int = None):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class ConnectionError(BackendError):
    pass


class BackendClient:
    def __init__(self, base_url: str = None):
        self.base_url = base_url or os.getenv("BACKEND_URL", "http://127.0.0.1:8000")

    def upload_file(self, file_path: str) -> dict:
        with open(file_path, "rb") as f:
            files = {"file": f}
            response = requests.post(f"{self.base_url}/hash", files=files, timeout=30)
        if response.status_code != 200:
            raise BackendError(response.json().get("detail", "Upload failed"), response.status_code)
        return response.json()

    def upload_file_bytes(self, file_bytes: bytes, filename: str) -> dict:
        files = {"file": (filename, file_bytes)}
        response = requests.post(f"{self.base_url}/hash", files=files, timeout=30)
        if response.status_code != 200:
            raise BackendError(response.json().get("detail", "Upload failed"), response.status_code)
        return response.json()

    def store_hash(self, hash_value: str) -> dict:
        response = requests.post(
            f"{self.base_url}/store",
            json={"hash": hash_value},
            timeout=30,
        )
        if response.status_code != 200:
            raise BackendError(response.json().get("detail", "Store failed"), response.status_code)
        return response.json()

    def verify_hash(self, hash_value: str) -> dict:
        response = requests.get(f"{self.base_url}/verify/{hash_value}", timeout=30)
        if response.status_code != 200:
            raise BackendError(response.json().get("detail", "Verify failed"), response.status_code)
        return response.json()
