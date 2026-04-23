import os
import json
from pathlib import Path
import bcrypt
import re

USERS_FILE = Path(__file__).parent / "data" / "users.json"
EMPLOYERS_FILE = Path(__file__).parent / "data" / "employers.json"
STUDENTS_FILE = Path(__file__).parent / "data" / "students.json"

EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")


def _ensure_users_file():
    USERS_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not USERS_FILE.exists():
        users = {
            "admin": {
                "password_hash": hash_password("admin123"),
                "institution": "Admin"
            }
        }
        with open(USERS_FILE, "w") as f:
            json.dump(users, f, indent=2)


def _ensure_employers_file():
    EMPLOYERS_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not EMPLOYERS_FILE.exists():
        with open(EMPLOYERS_FILE, "w") as f:
            json.dump({}, f, indent=2)


def _ensure_students_file():
    STUDENTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not STUDENTS_FILE.exists():
        with open(STUDENTS_FILE, "w") as f:
            json.dump({}, f, indent=2)


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))


def load_users() -> dict:
    _ensure_users_file()
    with open(USERS_FILE, "r") as f:
        return json.load(f)


def save_users(users: dict):
    _ensure_users_file()
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)


def authenticate(username: str, password: str) -> dict | None:
    users = load_users()
    if username not in users:
        return None
    user = users[username]
    if verify_password(password, user["password_hash"]):
        return {"username": username, "institution": user["institution"]}
    return None


def create_user(username: str, password: str, institution: str) -> bool:
    users = load_users()
    if username in users:
        return False
    users[username] = {
        "password_hash": hash_password(password),
        "institution": institution
    }
    save_users(users)
    return True


def is_logged_in():
    import streamlit as st
    return st.session_state.get("logged_in", False)


def login(username: str, institution: str):
    import streamlit as st
    st.session_state["logged_in"] = True
    st.session_state["username"] = username
    st.session_state["institution"] = institution


def logout():
    import streamlit as st
    st.session_state["logged_in"] = False
    st.session_state["username"] = None
    st.session_state["institution"] = None


def require_auth():
    import streamlit as st
    if not is_logged_in():
        st.warning("Please log in to access this page.")
        st.page_link("pages/Login.py", label="Go to Login")
        st.stop()


# ============== EMPLOYER AUTHENTICATION ==============

def load_employers() -> dict:
    _ensure_employers_file()
    with open(EMPLOYERS_FILE, "r") as f:
        return json.load(f)


def save_employers(employers: dict):
    _ensure_employers_file()
    with open(EMPLOYERS_FILE, "w") as f:
        json.dump(employers, f, indent=2)


def validate_employer_email(email: str) -> bool:
    """Validate employer email format."""
    return EMAIL_PATTERN.match(email) is not None


def register_employer(email: str, password: str, company_name: str) -> dict:
    """
    Register a new employer.
    Returns dict with 'success' (bool) and 'message' (str).
    """
    employers = load_employers()
    
    if not validate_employer_email(email):
        return {"success": False, "message": "Invalid email format"}
    
    if len(password) < 6:
        return {"success": False, "message": "Password must be at least 6 characters"}
    
    if not company_name.strip():
        return {"success": False, "message": "Company name is required"}
    
    if email in employers:
        return {"success": False, "message": "Email already registered"}
    
    employers[email] = {
        "password_hash": hash_password(password),
        "company_name": company_name.strip(),
        "created_at": str(Path(EMPLOYERS_FILE).stat().st_mtime if EMPLOYERS_FILE.exists() else ""),
    }
    save_employers(employers)
    
    return {"success": True, "message": "Registration successful"}


def authenticate_employer(email: str, password: str) -> dict | None:
    """
    Authenticate an employer.
    Returns employer data if successful, None otherwise.
    """
    employers = load_employers()
    
    if email not in employers:
        return None
    
    employer = employers[email]
    if verify_password(password, employer["password_hash"]):
        return {
            "email": email,
            "company_name": employer["company_name"],
        }
    return None


def is_employer_logged_in():
    import streamlit as st
    return st.session_state.get("employer_logged_in", False)


def employer_login(email: str, company_name: str):
    import streamlit as st
    st.session_state["employer_logged_in"] = True
    st.session_state["employer_email"] = email
    st.session_state["employer_company"] = company_name


def employer_logout():
    import streamlit as st
    st.session_state["employer_logged_in"] = False
    st.session_state["employer_email"] = None
    st.session_state["employer_company"] = None


def require_employer_auth():
    import streamlit as st
    if not is_employer_logged_in():
        st.warning("Please log in to access the Employer Portal.")
        st.page_link("pages/4_Employer_Login.py", label="Go to Employer Login")
        st.stop()


# ============== STUDENT AUTHENTICATION ==============

def load_students() -> dict:
    _ensure_students_file()
    with open(STUDENTS_FILE, "r") as f:
        return json.load(f)


def save_students(students: dict):
    _ensure_students_file()
    with open(STUDENTS_FILE, "w") as f:
        json.dump(students, f, indent=2)


def register_student(email: str, password: str, student_id: str = "", full_name: str = "") -> dict:
    """
    Register a new student.
    Returns dict with 'success' (bool) and 'message' (str).
    """
    students = load_students()
    
    if not validate_employer_email(email):
        return {"success": False, "message": "Invalid email format"}
    
    if len(password) < 4:
        return {"success": False, "message": "Password must be at least 4 characters"}
    
    if email in students:
        return {"success": False, "message": "Email already registered"}
    
    students[email] = {
        "password_hash": hash_password(password),
        "student_id": student_id.strip(),
        "full_name": full_name.strip(),
        "created_at": str(Path(STUDENTS_FILE).stat().st_mtime if STUDENTS_FILE.exists() else ""),
    }
    save_students(students)
    
    return {"success": True, "message": "Registration successful"}


def authenticate_student(email: str, password: str) -> dict | None:
    """
    Authenticate a student.
    Returns student data if successful, None otherwise.
    """
    students = load_students()
    
    if email not in students:
        return None
    
    student = students[email]
    if verify_password(password, student["password_hash"]):
        return {
            "email": email,
            "student_id": student.get("student_id", ""),
            "full_name": student.get("full_name", ""),
        }
    return None


def is_student_logged_in():
    import streamlit as st
    return st.session_state.get("student_logged_in", False)


def student_login(email: str, student_id: str = "", full_name: str = ""):
    import streamlit as st
    st.session_state["student_logged_in"] = True
    st.session_state["student_email"] = email
    st.session_state["student_id"] = student_id
    st.session_state["student_name"] = full_name


def student_logout():
    import streamlit as st
    st.session_state["student_logged_in"] = False
    st.session_state["student_email"] = None
    st.session_state["student_id"] = None
    st.session_state["student_name"] = None


def require_student_auth():
    import streamlit as st
    if not is_student_logged_in():
        st.warning("Please log in to access your transcripts.")
        st.page_link("pages/6_Student_Login.py", label="Go to Student Login")
        st.stop()
