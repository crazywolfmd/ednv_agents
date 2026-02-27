from __future__ import annotations

import streamlit as st

from streamlit_app.auth.service import sign_in


def render_auth_screen() -> None:
    st.subheader("Authentication")
    st.caption("Login with your username/email and password from caas_users table.")

    with st.form("login_form", clear_on_submit=False):
        login_identifier = st.text_input("Username or Email", key="login_identifier")
        login_password = st.text_input("Password", type="password", key="login_password")
        login_submitted = st.form_submit_button("Login", width="stretch")

    if login_submitted:
        ok, message = sign_in(login_identifier, login_password)
        if ok:
            st.success(message)
            st.rerun()
        else:
            st.error(message)

