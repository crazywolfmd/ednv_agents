from __future__ import annotations

from typing import Any

import bcrypt
import streamlit as st

from db.repository import get_caas_user_by_identifier


AUTH_STATE_KEY = "auth_state"


def init_auth_state() -> None:
    if AUTH_STATE_KEY not in st.session_state:
        st.session_state[AUTH_STATE_KEY] = {"user": None}


def _state() -> dict[str, Any]:
    init_auth_state()
    return st.session_state[AUTH_STATE_KEY]


def is_authenticated() -> bool:
    state = _state()
    return state.get("user") is not None


def get_current_user() -> dict[str, Any] | None:
    state = _state()
    return state.get("user")


def _verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except Exception:
        return False


def sign_in(identifier: str, password: str) -> tuple[bool, str]:
    identifier = identifier.strip()

    if not identifier or not password:
        return False, "Please enter both username/email and password."

    try:
        user = get_caas_user_by_identifier(identifier)
    except Exception:
        return False, "Login is temporarily unavailable. Please try again later."

    if not user:
        return False, "Invalid credentials."

    password_hash = user.get("password_hash")
    if not isinstance(password_hash, str) or not _verify_password(password, password_hash):
        return False, "Invalid credentials."

    state = _state()
    state["user"] = {
        "user_id": user.get("user_id"),
        "username": user.get("username"),
        "name": user.get("name"),
        "lastname": user.get("lastname"),
        "email": user.get("email"),
    }
    return True, "Logged in successfully."


def sign_out() -> None:
    clear_auth_state()


def clear_auth_state() -> None:
    st.session_state[AUTH_STATE_KEY] = {"user": None}
