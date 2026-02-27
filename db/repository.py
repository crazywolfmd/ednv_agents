from __future__ import annotations

from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from typing import Any

from db.client import create_supabase_client
from agents.settings import settings


def insert_row(table: str, payload: dict[str, Any]) -> Any:
    client = create_supabase_client()
    return client.table(table).insert(payload).execute()


def fetch_rows(table: str, limit: int = 20) -> Any:
    client = create_supabase_client()
    return client.table(table).select("*").limit(limit).execute()


def get_caas_user_by_identifier(identifier: str) -> dict[str, Any] | None:
    client = create_supabase_client()

    email_result = (
        client.table("caas_users")
        .select("user_id,username,name,lastname,email,password_hash,access_role,is_active")
        .eq("email", identifier)
        .limit(1)
        .execute()
    )
    if email_result.data:
        return email_result.data[0]

    username_result = (
        client.table("caas_users")
        .select("user_id,username,name,lastname,email,password_hash,access_role,is_active")
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


def insert_chat_message(
    user_id: str,
    role: str,
    content: str,
    llm_usage: dict[str, Any] | None = None,
) -> Any:
    client = create_supabase_client()
    payload: dict[str, Any] = {
        "user_id": user_id,
        "role": role,
        "content": content,
    }

    if llm_usage:
        payload.update(
            {
                "llm_provider": llm_usage.get("llm_provider") or settings.llm_provider,
                "llm_model": llm_usage.get("llm_model"),
                "llm_prompt_tokens": int(llm_usage.get("prompt_tokens", 0) or 0),
                "llm_completion_tokens": int(llm_usage.get("completion_tokens", 0) or 0),
                "llm_total_tokens": int(llm_usage.get("total_tokens", 0) or 0),
                "llm_calls": int(llm_usage.get("llm_calls", 0) or 0),
            }
        )

    return client.table("caas_chat_messages").insert(payload).execute()


def fetch_recent_chat_messages(user_id: str, limit: int = 20) -> list[dict[str, Any]]:
    client = create_supabase_client()
    result = (
        client.table("caas_chat_messages")
        .select("role,content,created_at")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return list(reversed(result.data or []))


def get_caas_accounts(user_id: str, only_active: bool = False) -> list[dict[str, Any]]:
    client = create_supabase_client()
    query = (
        client.table("caas_accounts")
        .select("account_id,user_id,account_type,currency,balance,status,opened_at,closed_at")
        .eq("user_id", user_id)
    )
    if only_active:
        query = query.eq("status", "active")
    result = query.execute()
    return result.data or []


def get_caas_account(user_id: str, account_id: str) -> dict[str, Any] | None:
    client = create_supabase_client()
    result = (
        client.table("caas_accounts")
        .select("account_id,user_id,account_type,currency,balance,status,opened_at,closed_at")
        .eq("user_id", user_id)
        .eq("account_id", account_id)
        .limit(1)
        .execute()
    )
    return result.data[0] if result.data else None


def create_caas_account(user_id: str, account_type: str, currency: str) -> dict[str, Any]:
    client = create_supabase_client()
    result = (
        client.table("caas_accounts")
        .insert(
            {
                "user_id": user_id,
                "account_type": account_type,
                "currency": currency.upper(),
                "status": "active",
            }
        )
        .execute()
    )
    return result.data[0]


def close_caas_account(user_id: str, account_id: str) -> dict[str, Any] | None:
    client = create_supabase_client()
    result = (
        client.table("caas_accounts")
        .update({"status": "closed", "closed_at": datetime.utcnow().isoformat()})
        .eq("user_id", user_id)
        .eq("account_id", account_id)
        .execute()
    )
    return result.data[0] if result.data else None


def get_caas_card(user_id: str, card_id: str) -> dict[str, Any] | None:
    client = create_supabase_client()
    result = (
        client.table("caas_cards")
        .select("card_id,user_id,linked_account_id,card_type,status,expires_at")
        .eq("user_id", user_id)
        .eq("card_id", card_id)
        .limit(1)
        .execute()
    )
    return result.data[0] if result.data else None


def create_caas_card(user_id: str, linked_account_id: str, card_type: str) -> dict[str, Any]:
    client = create_supabase_client()
    expires_on = date.today() + timedelta(days=365 * 3)
    result = (
        client.table("caas_cards")
        .insert(
            {
                "user_id": user_id,
                "linked_account_id": linked_account_id,
                "card_type": card_type,
                "status": "active",
                "expires_at": expires_on.isoformat(),
            }
        )
        .execute()
    )
    return result.data[0]


def close_caas_card(user_id: str, card_id: str) -> dict[str, Any] | None:
    client = create_supabase_client()
    result = (
        client.table("caas_cards")
        .update({"status": "closed", "closed_at": datetime.utcnow().isoformat()})
        .eq("user_id", user_id)
        .eq("card_id", card_id)
        .execute()
    )
    return result.data[0] if result.data else None


def list_recent_caas_transactions(user_id: str, limit: int = 10) -> list[dict[str, Any]]:
    client = create_supabase_client()
    result = (
        client.table("caas_transactions")
        .select("tx_id,tx_type,status,amount,currency,reason,created_at")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return result.data or []


def create_caas_transaction(payload: dict[str, Any]) -> dict[str, Any]:
    client = create_supabase_client()
    result = client.table("caas_transactions").insert(payload).execute()
    return result.data[0]


def _to_decimal(value: Any) -> Decimal:
    if isinstance(value, Decimal):
        return value
    if value is None:
        return Decimal("0")
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return Decimal("0")


def apply_internal_transfer(
    user_id: str,
    from_account_id: str,
    to_account_id: str,
    amount: Decimal,
    currency: str,
) -> dict[str, Any]:
    client = create_supabase_client()

    from_account = get_caas_account(user_id=user_id, account_id=from_account_id)
    to_account = get_caas_account(user_id=user_id, account_id=to_account_id)

    if not from_account or not to_account:
        return {"ok": False, "reason": "One or both accounts were not found."}

    if from_account.get("status") != "active" or to_account.get("status") != "active":
        return {"ok": False, "reason": "Both accounts must be active."}

    if from_account.get("currency") != currency or to_account.get("currency") != currency:
        return {"ok": False, "reason": "Currency mismatch on selected accounts."}

    from_balance = _to_decimal(from_account.get("balance"))
    if from_balance < amount:
        return {"ok": False, "reason": "Insufficient funds."}

    new_from_balance = str(from_balance - amount)
    new_to_balance = str(_to_decimal(to_account.get("balance")) + amount)

    client.table("caas_accounts").update({"balance": new_from_balance}).eq("account_id", from_account_id).eq("user_id", user_id).execute()
    client.table("caas_accounts").update({"balance": new_to_balance}).eq("account_id", to_account_id).eq("user_id", user_id).execute()

    tx = create_caas_transaction(
        {
            "user_id": user_id,
            "tx_type": "internal_transfer",
            "from_account_id": from_account_id,
            "to_account_id": to_account_id,
            "amount": str(amount),
            "currency": currency,
            "status": "approved",
            "reason": "Transfer completed.",
            "metadata": {},
        }
    )
    return {"ok": True, "transaction": tx}

def purge_old_chat_messages(user_id: str, days: int = 1) -> Any:
    client = create_supabase_client()
    cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
    return (
        client.table("caas_chat_messages")
        .delete()
        .eq("user_id", user_id)
        .lt("created_at", cutoff)
        .execute()
    )


def clear_chat_messages(user_id: str) -> Any:
    client = create_supabase_client()
    return client.table("caas_chat_messages").delete().eq("user_id", user_id).execute()

def _fetch_single_admin_view_row(view_name: str) -> dict[str, Any]:
    client = create_supabase_client()
    result = client.table(view_name).select("*").limit(1).execute()
    return (result.data or [{}])[0]


def _fetch_admin_view_rows(
    view_name: str,
    order_column: str | None = None,
    desc: bool = True,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    client = create_supabase_client()
    query = client.table(view_name).select("*")
    if order_column:
        query = query.order(order_column, desc=desc)
    if limit is not None:
        query = query.limit(limit)
    result = query.execute()
    return result.data or []


def get_admin_kpis() -> dict[str, Any]:
    return _fetch_single_admin_view_row("caas_admin_vw_kpis")


def get_admin_daily_usage(limit_days: int = 30) -> list[dict[str, Any]]:
    rows = _fetch_admin_view_rows(
        "caas_admin_vw_daily_usage",
        order_column="day",
        desc=True,
        limit=limit_days,
    )
    return list(reversed(rows))


def get_admin_provider_usage() -> list[dict[str, Any]]:
    return _fetch_admin_view_rows(
        "caas_admin_vw_provider_usage",
        order_column="total_tokens",
        desc=True,
    )


def get_admin_model_usage(limit_rows: int = 25) -> list[dict[str, Any]]:
    return _fetch_admin_view_rows(
        "caas_admin_vw_model_usage",
        order_column="total_tokens",
        desc=True,
        limit=limit_rows,
    )


def get_admin_transaction_daily(limit_days: int = 30) -> list[dict[str, Any]]:
    rows = _fetch_admin_view_rows(
        "caas_admin_vw_transaction_daily",
        order_column="day",
        desc=True,
    )
    return list(reversed(rows[: limit_days * 20]))


def get_admin_transaction_failures(limit_rows: int = 50) -> list[dict[str, Any]]:
    return _fetch_admin_view_rows(
        "caas_admin_vw_transaction_failures",
        order_column="created_at",
        desc=True,
        limit=limit_rows,
    )


def get_admin_auth_daily(limit_days: int = 30) -> list[dict[str, Any]]:
    rows = _fetch_admin_view_rows(
        "caas_admin_vw_auth_daily",
        order_column="day",
        desc=True,
    )
    return list(reversed(rows[: limit_days * 5]))


def get_admin_entity_status() -> list[dict[str, Any]]:
    return _fetch_admin_view_rows("caas_admin_vw_entity_status")


def get_admin_data_quality() -> dict[str, Any]:
    return _fetch_single_admin_view_row("caas_admin_vw_data_quality")


