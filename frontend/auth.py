import os
import json
from pathlib import Path
import bcrypt

USERS_FILE = Path(__file__).parent / "data" / "users.json"


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
