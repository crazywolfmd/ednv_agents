from __future__ import annotations

from typing import Any

from db.client import create_supabase_client


def insert_row(table: str, payload: dict[str, Any]) -> Any:
    client = create_supabase_client()
    return client.table(table).insert(payload).execute()


def fetch_rows(table: str, limit: int = 20) -> Any:
    client = create_supabase_client()
    return client.table(table).select("*").limit(limit).execute()


def get_caas_user_by_identifier(identifier: str) -> dict[str, Any] | None:
    client = create_supabase_client()

    # Check by email first.
    email_result = (
        client.table("caas_users")
        .select("user_id,username,name,lastname,email,password_hash")
        .eq("email", identifier)
        .limit(1)
        .execute()
    )
    if email_result.data:
        return email_result.data[0]

    # Fallback to username.
    username_result = (
        client.table("caas_users")
        .select("user_id,username,name,lastname,email,password_hash")
        .eq("username", identifier)
        .limit(1)
        .execute()
    )
    if username_result.data:
        return username_result.data[0]

    return None


def insert_caas_user_access_log(payload: dict[str, Any]) -> Any:
    client = create_supabase_client()
    return client.table("caas_user_access_logs").insert(payload).execute()
