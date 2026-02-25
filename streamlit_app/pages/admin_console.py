from __future__ import annotations

import streamlit as st

from db.client import create_supabase_client


PAGE_SIZE = 1000


def _get_user_count() -> int:
    client = create_supabase_client()
    result = client.table("caas_users").select("user_id", count="exact").limit(1).execute()
    return int(result.count or 0)


def _get_total_used_tokens() -> int:
    client = create_supabase_client()
    offset = 0
    total_tokens = 0

    while True:
        result = (
            client.table("caas_chat_messages")
            .select("llm_total_tokens")
            .not_.is_("llm_total_tokens", "null")
            .range(offset, offset + PAGE_SIZE - 1)
            .execute()
        )

        rows = result.data or []
        if not rows:
            break

        for row in rows:
            value = row.get("llm_total_tokens")
            if isinstance(value, int):
                total_tokens += value
            elif isinstance(value, str) and value.isdigit():
                total_tokens += int(value)

        if len(rows) < PAGE_SIZE:
            break
        offset += PAGE_SIZE

    return total_tokens


def render_page() -> None:
    st.subheader("Admin Analytics")
    st.caption("Visible only to admin users.")

    try:
        total_tokens = _get_total_used_tokens()
        user_count = _get_user_count()
    except Exception:
        st.error("Could not load analytics right now.")
        return

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Used Tokens", f"{total_tokens:,}")
    with col2:
        st.metric("User Count", f"{user_count:,}")
