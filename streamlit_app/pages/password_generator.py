from __future__ import annotations

import bcrypt
import streamlit as st


def render_page() -> None:
    st.subheader("Password Hash Generator")
    st.caption("Generate bcrypt hash values for caas_users.password_hash")

    plain_password = st.text_input("Password", type="password")

    if st.button("Generate Hash", type="primary", use_container_width=True):
        if not plain_password:
            st.warning("Please enter a password.")
            return

        try:
            hashed = bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        except Exception:
            st.error("Could not generate hash right now. Please try again.")
            return

        st.success("Hash generated.")
        st.code(hashed)
