from __future__ import annotations

import logging

import streamlit as st

from agents.graph import build_graph
from db.repository import clear_chat_messages, fetch_recent_chat_messages, insert_chat_message, purge_old_chat_messages
from streamlit_app.auth.service import get_current_user, init_auth_state, is_authenticated, sign_out
from streamlit_app.auth.ui import render_auth_screen
from streamlit_app.pages.admin_console import render_page as render_admin_console_page
from streamlit_app.pages.password_generator import render_page as render_password_generator_page
from streamlit_app.pages.system_status import render_page as render_system_status_page
from streamlit_app.settings import APP_CAPTION, APP_TITLE, DEFAULT_PLACEHOLDER


logger = logging.getLogger(__name__)


def _load_history_once(user_id: str) -> None:
    if st.session_state.get("history_loaded"):
        return

    try:
        purge_old_chat_messages(user_id=user_id, days=1)
    except Exception:
        logger.exception("Daily chat cleanup failed.")

    try:
        rows = fetch_recent_chat_messages(user_id=user_id, limit=5000)
    except Exception:
        st.session_state.history = []
        st.session_state.history_loaded = True
        return

    history: list[dict[str, str]] = []
    pending_user = None
    for row in rows:
        role = row.get("role")
        content = row.get("content", "")
        if role == "user":
            pending_user = content
        elif role == "assistant":
            history.append({"user": pending_user or "", "assistant": content})
            pending_user = None

    st.session_state.history = history
    st.session_state.history_loaded = True


def _persist_turn(
    user_id: str,
    user_text: str,
    assistant_text: str,
    llm_usage: dict[str, int | str] | None = None,
) -> None:
    try:
        insert_chat_message(user_id=user_id, role="user", content=user_text)
        insert_chat_message(
            user_id=user_id,
            role="assistant",
            content=assistant_text,
            llm_usage=llm_usage,
        )
    except Exception:
        logger.exception("Failed to persist chat messages.")


def _render_chat(user: dict[str, str]) -> None:
    graph = build_graph()
    user_id = str(user.get("user_id", ""))

    if "history" not in st.session_state:
        st.session_state.history = []
    if "pending_action" not in st.session_state:
        st.session_state.pending_action = None
    if "history_loaded" not in st.session_state:
        st.session_state.history_loaded = False

    _load_history_once(user_id=user_id)

    if st.session_state.pending_action:
        st.info("A transaction is pending confirmation. Type CONFIRM to execute or CANCEL to abort.")

    with st.form("chat_input_form", clear_on_submit=True):
        user_input = st.text_input("Ask anything", placeholder=DEFAULT_PLACEHOLDER)
        send_clicked = st.form_submit_button("Send", type="primary", use_container_width=True)

    if send_clicked and user_input.strip():
        try:
            result = graph.invoke(
                {
                    "user_input": user_input,
                    "user_id": user_id,
                    "pending_action": st.session_state.pending_action,
                    "assistant_response": "",
                    "token_usage": {},
                }
            )
            answer = result.get("assistant_response", "")
            llm_usage = result.get("token_usage", {})
            st.session_state.pending_action = result.get("pending_action")
        except Exception as exc:
            logger.exception("Chat processing failed.")
            st.exception(exc)
            return

        st.session_state.history.append({"user": user_input, "assistant": answer})
        _persist_turn(
            user_id=user_id,
            user_text=user_input,
            assistant_text=answer,
            llm_usage=llm_usage,
        )
        st.rerun()

    st.markdown("### Conversation")
    for turn in st.session_state.history:
        st.markdown(f"**You:** {turn['user']}")
        st.markdown("**Assistant:**")
        st.markdown(turn["assistant"])

    left_col, right_col = st.columns([9, 1])
    with right_col:
        if st.button("Clear", key="clear_chat_btn", use_container_width=False, help="Clear today's chat history"):
            try:
                clear_chat_messages(user_id=user_id)
            except Exception as exc:
                logger.exception("Failed to clear chat messages.")
                st.exception(exc)
                return

            st.session_state.history = []
            st.session_state.pending_action = None
            st.session_state.history_loaded = True
            st.rerun()


def run() -> None:
    st.set_page_config(page_title=APP_TITLE, page_icon=":robot_face:")
    st.title(APP_TITLE)
    st.caption(APP_CAPTION)

    init_auth_state()

    if not is_authenticated():
        render_auth_screen()
        return

    user = get_current_user()
    if not user:
        render_auth_screen()
        return

    access_role = str(user.get("access_role") or "user")
    is_admin = access_role == "admin"

    display_name = user.get("username") or user.get("email") or "user"
    st.sidebar.success(f"Logged in as {display_name}")
    st.sidebar.caption(f"Role: {access_role}")

    if st.sidebar.button("Logout", use_container_width=True):
        sign_out()
        st.session_state.history = []
        st.session_state.history_loaded = False
        st.session_state.pending_action = None
        st.rerun()

    requested_page = st.query_params.get("page", "")
    if requested_page == "password-generator":
        try:
            render_password_generator_page()
        except Exception as exc:
            logger.exception("Password generator page failed.")
            st.exception(exc)
        return

    if requested_page == "admin-console":
        if not is_admin:
            st.error("You are not authorized to access this page.")
            return
        try:
            render_admin_console_page()
        except Exception as exc:
            logger.exception("Admin console page failed.")
            st.exception(exc)
        return

    nav_items = ["Chat", "Password Generator", "System Status"]
    if is_admin:
        nav_items.append("Admin Console")

    selected_page = st.sidebar.radio("Navigation", nav_items)

    if selected_page == "Password Generator":
        try:
            render_password_generator_page()
        except Exception as exc:
            logger.exception("Password generator page failed.")
            st.exception(exc)
        return

    if selected_page == "System Status":
        try:
            render_system_status_page()
        except Exception as exc:
            logger.exception("System Status page failed.")
            st.exception(exc)
        return

    if selected_page == "Admin Console":
        if not is_admin:
            st.error("You are not authorized to access this page.")
            return
        try:
            render_admin_console_page()
        except Exception as exc:
            logger.exception("Admin console page failed.")
            st.exception(exc)
        return

    _render_chat(user=user)


if __name__ == "__main__":
    try:
        run()
    except Exception as exc:
        logger.exception("Unhandled app error.")
        st.exception(exc)

