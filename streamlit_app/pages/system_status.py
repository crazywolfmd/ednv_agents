from __future__ import annotations

import streamlit as st

from db.client import get_supabase_config


def render_page() -> None:
    st.subheader("System Status")

    config = get_supabase_config()

    if config["url"] and config["key"]:
        st.success("Supabase environment variables are configured.")
    else:
        st.warning("Supabase is not fully configured. Set SUPABASE_URL and SUPABASE_ANON_KEY in secrets or .env")

    st.write("This page is a starter placeholder for app diagnostics.")
