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


class DuplicateError(BackendError):
    pass


class BackendClient:
    def __init__(self, base_url: str = None, frontend_url: str = None):
        self.base_url = base_url or os.getenv("BACKEND_URL", "http://127.0.0.1:8000")
        self.frontend_url = frontend_url or os.getenv("FRONTEND_URL", "http://localhost:8501")

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
        if response.status_code == 409:
            raise DuplicateError(response.json().get("detail", "Transcript already issued"), response.status_code)
        if response.status_code != 200:
            raise BackendError(response.json().get("detail", "Store failed"), response.status_code)
        return response.json()

    def verify_hash(self, hash_value: str) -> dict:
        response = requests.get(f"{self.base_url}/verify/{hash_value}", timeout=30)
        if response.status_code != 200:
            raise BackendError(response.json().get("detail", "Verify failed"), response.status_code)
        return response.json()

    def get_verification_url(self, hash_value: str) -> str:
        return f"{self.frontend_url}/pages/3_Student.py?verify={hash_value}"

    def get_transcript(self, hash_value: str) -> dict | None:
        response = requests.get(f"{self.base_url}/transcript/{hash_value}", timeout=30)
        if response.status_code == 404:
            return None
        if response.status_code != 200:
            raise BackendError(response.json().get("detail", "Failed to get transcript"), response.status_code)
        return response.json()

    def store_file(self, file_bytes: bytes, filename: str) -> dict:
        files = {"file": (filename, file_bytes)}
        response = requests.post(f"{self.base_url}/store-file", files=files, timeout=60)
        if response.status_code != 200:
            raise BackendError(response.json().get("detail", "Store file failed"), response.status_code)
        return response.json()

    def get_file_status(self, hash_value: str) -> dict:
        response = requests.get(f"{self.base_url}/file-status/{hash_value}", timeout=30)
        if response.status_code != 200:
            raise BackendError(response.json().get("detail", "Failed to get file status"), response.status_code)
        return response.json()

    def get_download_url(self, hash_value: str) -> str:
        return f"{self.base_url}/download/{hash_value}"
