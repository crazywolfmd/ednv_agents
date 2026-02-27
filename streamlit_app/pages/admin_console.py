from __future__ import annotations

import pandas as pd
import streamlit as st

from db.repository import (
    get_admin_auth_daily,
    get_admin_daily_usage,
    get_admin_data_quality,
    get_admin_entity_status,
    get_admin_kpis,
    get_admin_model_usage,
    get_admin_provider_usage,
    get_admin_transaction_daily,
    get_admin_transaction_failures,
)


def _as_int(value: object) -> int:
    if value is None:
        return 0
    if isinstance(value, int):
        return value
    try:
        return int(value)
    except Exception:
        return 0


def _safe_dataframe(rows: list[dict]) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows)


def render_page() -> None:
    st.subheader("Admin Analytics Dashboard")
    st.caption("Operational metrics for users, LLM usage, transactions, auth events, and data quality.")

    try:
        kpis = get_admin_kpis()
        daily_usage = get_admin_daily_usage(limit_days=30)
        provider_usage = get_admin_provider_usage()
        model_usage = get_admin_model_usage(limit_rows=30)
        tx_daily = get_admin_transaction_daily(limit_days=30)
        tx_failures = get_admin_transaction_failures(limit_rows=30)
        auth_daily = get_admin_auth_daily(limit_days=30)
        entity_status = get_admin_entity_status()
        quality = get_admin_data_quality()
    except Exception:
        st.error("Could not load analytics right now.")
        return

    top_cols = st.columns(4)
    with top_cols[0]:
        st.metric("Users", f"{_as_int(kpis.get('total_users')):,}")
        st.caption(f"Active: {_as_int(kpis.get('active_users')):,}")
    with top_cols[1]:
        st.metric("Total Tokens", f"{_as_int(kpis.get('total_tokens')):,}")
        st.caption(f"LLM Calls: {_as_int(kpis.get('total_llm_calls')):,}")
    with top_cols[2]:
        st.metric("Chat Messages", f"{_as_int(kpis.get('total_chat_messages')):,}")
        st.caption(f"Assistant: {_as_int(kpis.get('assistant_messages')):,}")
    with top_cols[3]:
        st.metric("Transactions", f"{_as_int(kpis.get('total_transactions')):,}")
        st.caption(f"Approved: {_as_int(kpis.get('approved_transactions')):,}")

    st.divider()

    st.markdown("### Usage Trend (Last 30 Days)")
    daily_df = _safe_dataframe(daily_usage)
    if daily_df.empty:
        st.info("No daily usage data yet.")
    else:
        daily_df["day"] = pd.to_datetime(daily_df["day"])
        chart_df = daily_df.set_index("day")[["total_messages", "assistant_messages", "total_tokens"]]
        st.line_chart(chart_df)
        st.dataframe(daily_df.sort_values("day", ascending=False), use_container_width=True)

    st.markdown("### Provider And Model Usage")
    provider_df = _safe_dataframe(provider_usage)
    model_df = _safe_dataframe(model_usage)

    left_col, right_col = st.columns(2)
    with left_col:
        st.caption("By provider")
        if provider_df.empty:
            st.info("No provider usage data yet.")
        else:
            st.bar_chart(provider_df.set_index("llm_provider")[["total_tokens", "assistant_messages"]])
            st.dataframe(provider_df, use_container_width=True)
    with right_col:
        st.caption("Top models")
        if model_df.empty:
            st.info("No model usage data yet.")
        else:
            st.dataframe(model_df, use_container_width=True)

    st.markdown("### Transaction Analytics")
    tx_daily_df = _safe_dataframe(tx_daily)
    tx_fail_df = _safe_dataframe(tx_failures)
    tx_cols = st.columns(3)
    with tx_cols[0]:
        st.metric("Rejected", f"{_as_int(kpis.get('rejected_transactions')):,}")
    with tx_cols[1]:
        st.metric("Pending", f"{_as_int(kpis.get('pending_transactions')):,}")
    with tx_cols[2]:
        st.metric("Approved", f"{_as_int(kpis.get('approved_transactions')):,}")

    if not tx_daily_df.empty:
        tx_daily_df["day"] = pd.to_datetime(tx_daily_df["day"])
        pivot_tx = (
            tx_daily_df.pivot_table(
                index="day",
                columns="status",
                values="tx_count",
                aggfunc="sum",
                fill_value=0,
            )
            .sort_index()
        )
        st.area_chart(pivot_tx)
        st.dataframe(tx_daily_df.sort_values("day", ascending=False), use_container_width=True)
    else:
        st.info("No transaction history yet.")

    st.caption("Recent failures or pending")
    if tx_fail_df.empty:
        st.info("No failed/pending transactions.")
    else:
        st.dataframe(tx_fail_df, use_container_width=True)

    st.markdown("### Auth Events")
    auth_df = _safe_dataframe(auth_daily)
    if auth_df.empty:
        st.info("No auth event data yet.")
    else:
        auth_df["day"] = pd.to_datetime(auth_df["day"])
        pivot_auth = (
            auth_df.pivot_table(
                index="day",
                columns="event_type",
                values="event_count",
                aggfunc="sum",
                fill_value=0,
            )
            .sort_index()
        )
        st.bar_chart(pivot_auth)
        st.dataframe(auth_df.sort_values("day", ascending=False), use_container_width=True)

    st.markdown("### Entity Status")
    entity_df = _safe_dataframe(entity_status)
    if entity_df.empty:
        st.info("No account/card status data yet.")
    else:
        st.dataframe(entity_df, use_container_width=True)

    st.markdown("### Data Quality")
    quality_cols = st.columns(5)
    with quality_cols[0]:
        st.metric("Missing Total Tokens", f"{_as_int(quality.get('assistant_missing_total_tokens')):,}")
    with quality_cols[1]:
        st.metric("Missing Provider", f"{_as_int(quality.get('assistant_missing_provider')):,}")
    with quality_cols[2]:
        st.metric("Missing Model", f"{_as_int(quality.get('assistant_missing_model')):,}")
    with quality_cols[3]:
        st.metric("Negative Token Rows", f"{_as_int(quality.get('assistant_negative_token_rows')):,}")
    with quality_cols[4]:
        st.metric("Access Logs Missing IP", f"{_as_int(quality.get('access_logs_missing_ip')):,}")

    refreshed_at = str(quality.get("refreshed_at") or "")
    if refreshed_at:
        st.caption(f"Analytics snapshot refreshed at: {refreshed_at}")
