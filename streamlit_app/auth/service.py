from __future__ import annotations

from typing import Any

import bcrypt
import streamlit as st

from db.repository import get_caas_user_by_identifier, insert_caas_user_access_log


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


def _get_request_metadata() -> dict[str, str | None]:
    ip_address = None
    user_agent = None

    try:
        headers = st.context.headers
        forwarded_for = headers.get("X-Forwarded-For")
        real_ip = headers.get("X-Real-Ip")
        user_agent = headers.get("User-Agent")

        if forwarded_for:
            ip_address = forwarded_for.split(",")[0].strip()
        elif real_ip:
            ip_address = real_ip
    except Exception:
        pass

    return {"ip_address": ip_address, "user_agent": user_agent}


def _log_access_event(
    event_type: str,
    identifier: str | None = None,
    user_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    request_metadata = _get_request_metadata()
    payload: dict[str, Any] = {
        "event_type": event_type,
        "identifier": identifier,
        "user_id": user_id,
        "ip_address": request_metadata.get("ip_address"),
        "user_agent": request_metadata.get("user_agent"),
        "metadata": metadata or {},
    }

    try:
        insert_caas_user_access_log(payload)
    except Exception:
        pass


def sign_in(identifier: str, password: str) -> tuple[bool, str]:
    identifier = identifier.strip()

    if not identifier or not password:
        return False, "Please enter both username/email and password."

    try:
        user = get_caas_user_by_identifier(identifier)
    except Exception:
        _log_access_event(
            event_type="login_failed",
            identifier=identifier,
            metadata={"reason": "lookup_unavailable"},
        )
        return False, "Login is temporarily unavailable. Please try again later."

    if not user:
        _log_access_event(
            event_type="login_failed",
            identifier=identifier,
            metadata={"reason": "user_not_found"},
        )
        return False, "Invalid credentials."

    if user.get("is_active") is False:
        _log_access_event(
            event_type="login_failed",
            identifier=identifier,
            user_id=user.get("user_id"),
            metadata={"reason": "inactive_user"},
        )
        return False, "This user is inactive. Please contact support."

    password_hash = user.get("password_hash")
    if not isinstance(password_hash, str) or not _verify_password(password, password_hash):
        _log_access_event(
            event_type="login_failed",
            identifier=identifier,
            user_id=user.get("user_id"),
            metadata={"reason": "invalid_password"},
        )
        return False, "Invalid credentials."

    state = _state()
    state["user"] = {
        "user_id": user.get("user_id"),
        "username": user.get("username"),
        "name": user.get("name"),
        "lastname": user.get("lastname"),
        "email": user.get("email"),
        "access_role": user.get("access_role") or "user",
    }

    _log_access_event(
        event_type="login_success",
        identifier=identifier,
        user_id=user.get("user_id"),
    )
    return True, "Logged in successfully."


def sign_out() -> None:
    current_user = get_current_user()
    if current_user:
        _log_access_event(
            event_type="logout",
            identifier=current_user.get("username") or current_user.get("email"),
            user_id=current_user.get("user_id"),
        )
    clear_auth_state()


def clear_auth_state() -> None:
    st.session_state[AUTH_STATE_KEY] = {"user": None}
