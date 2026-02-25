from __future__ import annotations

import logging

import streamlit as st

from agents.graph import build_graph
from streamlit_app.auth.service import get_current_user, init_auth_state, is_authenticated, sign_out
from streamlit_app.auth.ui import render_auth_screen
from streamlit_app.pages.password_generator import render_page as render_password_generator_page
from streamlit_app.pages.system_status import render_page as render_system_status_page
from streamlit_app.settings import APP_CAPTION, APP_TITLE, DEFAULT_PLACEHOLDER


logger = logging.getLogger(__name__)


def _render_chat() -> None:
    graph = build_graph()

    if "history" not in st.session_state:
        st.session_state.history = []

    for turn in st.session_state.history:
        st.markdown(f"**You:** {turn['user']}")
        st.markdown(f"**Assistant:** {turn['assistant']}")

    user_input = st.text_input("Ask anything", placeholder=DEFAULT_PLACEHOLDER)

    if st.button("Send", type="primary", use_container_width=True) and user_input.strip():
        try:
            result = graph.invoke({"user_input": user_input, "response": ""})
            answer = result["response"]
        except Exception:
            logger.exception("Chat processing failed.")
            st.error("Sorry, I could not process your request right now. Please try again.")
            return

        st.session_state.history.append({"user": user_input, "assistant": answer})
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

    display_name = user.get("username") or user.get("email") or "user"
    st.sidebar.success(f"Logged in as {display_name}")
    if st.sidebar.button("Logout", use_container_width=True):
        sign_out()
        st.session_state.history = []
        st.rerun()

    requested_page = st.query_params.get("page", "")
    if requested_page == "password-generator":
        try:
            render_password_generator_page()
        except Exception:
            logger.exception("Password generator page failed.")
            st.error("The page is temporarily unavailable. Please refresh and try again.")
        return

    selected_page = st.sidebar.radio(
        "Navigation",
        ["Chat", "Password Generator", "System Status"],
    )

    if selected_page == "Password Generator":
        try:
            render_password_generator_page()
        except Exception:
            logger.exception("Password generator page failed.")
            st.error("The page is temporarily unavailable. Please refresh and try again.")
        return

    if selected_page == "System Status":
        try:
            render_system_status_page()
        except Exception:
            logger.exception("System Status page failed.")
            st.error("The page is temporarily unavailable. Please refresh and try again.")
        return

    _render_chat()


if __name__ == "__main__":
    try:
        run()
    except Exception:
        logger.exception("Unhandled app error.")
        st.error("Something went wrong. Please refresh and try again.")
