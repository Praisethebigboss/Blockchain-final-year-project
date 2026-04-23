import os
import requests
from dotenv import load_dotenv

load_dotenv()


class BackendError(Exception):
    def __init__(self, message: str, status_code: int = None):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class DuplicateError(BackendError):
    pass


class BackendClient:
    def __init__(self, base_url: str = None, frontend_url: str = None):
        self.base_url = base_url or os.getenv("BACKEND_URL", "http://127.0.0.1:8889")
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
        try:
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
        except requests.exceptions.RequestException as e:
            raise BackendError(str(e), 503)

    def verify_hash(self, hash_value: str) -> dict:
        try:
            response = requests.get(f"{self.base_url}/verify/{hash_value}", timeout=10)
            if response.status_code != 200:
                raise BackendError(response.json().get("detail", "Verify failed"), response.status_code)
            return response.json()
        except requests.exceptions.RequestException as e:
            raise BackendError(str(e), 503)

    def get_verification_url(self, hash_value: str) -> str:
        return f"{self.frontend_url}/pages/3_Student.py?verify={hash_value}"

    def get_transcript(self, hash_value: str) -> dict | None:
        try:
            response = requests.get(f"{self.base_url}/transcript/{hash_value}", timeout=10)
            if response.status_code == 404:
                return None
            if response.status_code != 200:
                raise BackendError(response.json().get("detail", "Failed to get transcript"), response.status_code)
            return response.json()
        except requests.exceptions.RequestException as e:
            raise BackendError(str(e), 503)

    def store_file(self, file_bytes: bytes, filename: str) -> dict:
        try:
            files = {"file": (filename, file_bytes)}
            response = requests.post(f"{self.base_url}/store-file", files=files, timeout=30)
            if response.status_code != 200:
                raise BackendError(response.json().get("detail", "Store file failed"), response.status_code)
            return response.json()
        except requests.exceptions.RequestException as e:
            raise BackendError(str(e), 503)

    def get_file_status(self, hash_value: str) -> dict:
        try:
            response = requests.get(f"{self.base_url}/file-status/{hash_value}", timeout=10)
            if response.status_code != 200:
                raise BackendError(response.json().get("detail", "Failed to get file status"), response.status_code)
            return response.json()
        except requests.exceptions.RequestException as e:
            raise BackendError(str(e), 503)

    def get_download_url(self, hash_value: str) -> str:
        return f"{self.base_url}/download/{hash_value}"

    def download_file(self, hash_value: str) -> dict:
        try:
            response = requests.get(
                f"{self.base_url}/download/{hash_value}",
                timeout=30,
            )
            if response.status_code == 404:
                raise BackendError("File not found", 404)
            if response.status_code != 200:
                raise BackendError("Download failed", response.status_code)
            content_disposition = response.headers.get("Content-Disposition", "")
            filename = "transcript.bin"
            if "filename=" in content_disposition:
                filename = content_disposition.split("filename=")[1].strip('"')
            return {
                "data": response.content,
                "filename": filename,
            }
        except requests.exceptions.RequestException as e:
            raise BackendError(str(e), 503)

    def list_transcripts(self, offset: int = 0, limit: int = 20) -> dict:
        try:
            response = requests.get(
                f"{self.base_url}/transcripts",
                params={"offset": offset, "limit": limit},
                timeout=10,
            )
            if response.status_code != 200:
                raise BackendError(response.json().get("detail", "Failed to list transcripts"), response.status_code)
            return response.json()
        except requests.exceptions.RequestException as e:
            raise BackendError(str(e), 503)

    def batch_store(self, file_list: list[tuple]) -> dict:
        try:
            files = [("files", (name, data)) for name, data in file_list]
            response = requests.post(f"{self.base_url}/batch-store", files=files, timeout=120)
            if response.status_code != 200:
                raise BackendError(response.json().get("detail", "Batch store failed"), response.status_code)
            return response.json()
        except requests.exceptions.RequestException as e:
            raise BackendError(str(e), 503)

    def generate_student_token(
        self,
        hash_value: str,
        student_email: str = "",
        student_name: str = "",
        institution: str = "University",
    ) -> dict:
        """Generate a student access token for a transcript."""
        try:
            response = requests.post(
                f"{self.base_url}/token/student",
                json={
                    "hash_value": hash_value,
                    "student_email": student_email,
                    "student_name": student_name,
                    "institution": institution,
                },
                timeout=30,
            )
            if response.status_code != 200:
                raise BackendError(response.json().get("detail", "Token generation failed"), response.status_code)
            return response.json()
        except requests.exceptions.RequestException as e:
            raise BackendError(str(e), 503)

    def get_verification_url_with_token(self, hash_value: str, token: str) -> str:
        """Get verification URL with token included."""
        return f"{self.frontend_url}/pages/3_Student.py?verify={hash_value}&token={token}"

    def validate_student_token(self, hash_value: str, token: str) -> dict:
        """Validate a student access token."""
        try:
            response = requests.get(
                f"{self.base_url}/token/student/validate",
                params={"hash_value": hash_value, "token": token},
                timeout=10,
            )
            if response.status_code != 200:
                raise BackendError(response.json().get("detail", "Token validation failed"), response.status_code)
            return response.json()
        except requests.exceptions.RequestException as e:
            raise BackendError(str(e), 503)

    def use_student_token(self, hash_value: str) -> dict:
        """Mark a student token as used after download."""
        try:
            response = requests.post(
                f"{self.base_url}/token/student/use",
                params={"hash_value": hash_value},
                timeout=10,
            )
            if response.status_code != 200:
                raise BackendError(response.json().get("detail", "Token use failed"), response.status_code)
            return response.json()
        except requests.exceptions.RequestException as e:
            raise BackendError(str(e), 503)

    def send_transcript_email(
        self,
        student_email: str,
        student_name: str,
        hash_value: str,
        verification_url: str,
        institution: str = "University",
    ) -> dict:
        """Send transcript notification email to student (mock)."""
        try:
            response = requests.post(
                f"{self.base_url}/email/send",
                json={
                    "student_email": student_email,
                    "student_name": student_name,
                    "hash_value": hash_value,
                    "verification_url": verification_url,
                    "institution": institution,
                },
                timeout=30,
            )
            if response.status_code != 200:
                raise BackendError(response.json().get("detail", "Email send failed"), response.status_code)
            return response.json()
        except requests.exceptions.RequestException as e:
            raise BackendError(str(e), 503)

    def get_student_transcripts(self, student_email: str) -> dict:
        """Get all transcripts for a student email."""
        try:
            response = requests.get(
                f"{self.base_url}/student/transcripts",
                params={"student_email": student_email},
                timeout=10,
            )
            if response.status_code != 200:
                raise BackendError(response.json().get("detail", "Failed to get transcripts"), response.status_code)
            return response.json()
        except requests.exceptions.RequestException as e:
            raise BackendError(str(e), 503)