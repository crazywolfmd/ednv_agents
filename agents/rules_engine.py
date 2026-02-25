from __future__ import annotations

from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any

from db.repository import (
    apply_internal_transfer,
    create_caas_account,
    create_caas_card,
    create_caas_transaction,
    get_caas_account,
    get_caas_accounts,
    get_caas_card,
    list_recent_caas_transactions,
)


def _parse_decimal(value: Any) -> Decimal | None:
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return None
    if amount <= 0:
        return None
    return amount


def _fmt_account(account: dict[str, Any]) -> str:
    return (
        f"{account.get('account_id')} | {account.get('account_type')} | "
        f"{account.get('currency')} {account.get('balance')} | {account.get('status')}"
    )


def _build_confirm_message(summary: str) -> str:
    return f"{summary}\n\nReply with CONFIRM to execute this request or CANCEL to abort."


def handle_rules_and_execution(
    *,
    user_id: str,
    user_input: str,
    intent: str,
    params: dict[str, Any],
    pending_action: dict[str, Any] | None,
) -> tuple[str, dict[str, Any] | None]:
    normalized = user_input.strip().upper()

    if normalized == "CANCEL" and pending_action:
        return "Pending action canceled.", None

    if normalized == "CONFIRM" and pending_action:
        pending_intent = pending_action.get("intent")
        pending_params = pending_action.get("params", {})

        if pending_intent == "transfer_between_accounts":
            amount = _parse_decimal(pending_params.get("amount"))
            if amount is None:
                return "Pending transfer is invalid. Please create it again.", None

            result = apply_internal_transfer(
                user_id=user_id,
                from_account_id=str(pending_params.get("from_account_id", "")),
                to_account_id=str(pending_params.get("to_account_id", "")),
                amount=amount,
                currency=str(pending_params.get("currency", "")).upper(),
            )
            if not result.get("ok"):
                return f"Transfer failed: {result.get('reason', 'unknown error')}", None
            tx = result.get("transaction", {})
            return f"Transfer completed successfully. Reference: TX-{tx.get('tx_id')}", None

        if pending_intent == "open_account":
            account = create_caas_account(
                user_id=user_id,
                account_type=str(pending_params.get("account_type", "checking")).lower(),
                currency=str(pending_params.get("currency", "USD")).upper(),
            )
            create_caas_transaction(
                {
                    "user_id": user_id,
                    "tx_type": "account_open",
                    "status": "approved",
                    "reason": "Account opened.",
                    "metadata": {"account_id": account.get("account_id")},
                }
            )
            return f"Account opened: {account.get('account_id')}", None

        if pending_intent == "open_card":
            linked_account_id = str(pending_params.get("linked_account_id", ""))
            account = get_caas_account(user_id=user_id, account_id=linked_account_id)
            if not account or account.get("status") != "active":
                return "Cannot open card. Linked account must exist and be active.", None

            card = create_caas_card(
                user_id=user_id,
                linked_account_id=linked_account_id,
                card_type=str(pending_params.get("card_type", "debit")).lower(),
            )
            create_caas_transaction(
                {
                    "user_id": user_id,
                    "tx_type": "card_open",
                    "status": "approved",
                    "reason": "Card opened.",
                    "metadata": {"card_id": card.get("card_id")},
                }
            )
            return f"Card opened: {card.get('card_id')} (expires {card.get('expires_at')})", None

        if pending_intent == "close_card":
            card = get_caas_card(user_id=user_id, card_id=str(pending_params.get("card_id", "")))
            if not card:
                return "Card was not found.", None
            if card.get("status") in {"closed", "expired"}:
                return "Card is already closed/expired.", None
            from db.repository import close_caas_card

            close_caas_card(user_id=user_id, card_id=str(card.get("card_id")))
            create_caas_transaction(
                {
                    "user_id": user_id,
                    "tx_type": "card_close",
                    "status": "approved",
                    "reason": "Card closed.",
                    "metadata": {"card_id": card.get("card_id")},
                }
            )
            return f"Card closed: {card.get('card_id')}", None

        if pending_intent == "close_account":
            account = get_caas_account(user_id=user_id, account_id=str(pending_params.get("account_id", "")))
            if not account:
                return "Account was not found.", None
            if Decimal(str(account.get("balance", "0"))) > Decimal("0"):
                return "Account closure denied. Balance must be zero.", None
            if account.get("status") == "closed":
                return "Account is already closed.", None
            from db.repository import close_caas_account

            close_caas_account(user_id=user_id, account_id=str(account.get("account_id")))
            create_caas_transaction(
                {
                    "user_id": user_id,
                    "tx_type": "account_close",
                    "status": "approved",
                    "reason": "Account closed.",
                    "metadata": {"account_id": account.get("account_id")},
                }
            )
            return f"Account closed: {account.get('account_id')}", None

        return "Unknown pending action. Please submit the request again.", None

    if intent == "check_balance":
        account_id = str(params.get("account_id", "")).strip()
        if account_id:
            account = get_caas_account(user_id=user_id, account_id=account_id)
            if not account:
                return "Account not found.", None
            return f"Balance for {account_id}: {account.get('currency')} {account.get('balance')}", None

        accounts = get_caas_accounts(user_id=user_id, only_active=False)
        if not accounts:
            return "No accounts found.", None
        lines = ["Your accounts:"] + [f"- {_fmt_account(account)}" for account in accounts]
        return "\n".join(lines), None

    if intent == "list_recent_transactions":
        rows = list_recent_caas_transactions(user_id=user_id, limit=10)
        if not rows:
            return "No recent transactions found.", None
        lines = ["Recent transactions:"]
        for row in rows:
            lines.append(
                f"- TX-{row.get('tx_id')} | {row.get('tx_type')} | {row.get('status')} | "
                f"{row.get('currency', '')} {row.get('amount', '')}"
            )
        return "\n".join(lines), None

    if intent == "transfer_between_accounts":
        from_account_id = str(params.get("from_account_id", "")).strip()
        to_account_id = str(params.get("to_account_id", "")).strip()
        currency = str(params.get("currency", "USD")).upper().strip()
        amount = _parse_decimal(params.get("amount"))

        if not from_account_id or not to_account_id or amount is None:
            return (
                "Transfer requires from_account_id, to_account_id, and amount > 0.",
                None,
            )

        if from_account_id == to_account_id:
            return "Transfer requires two different accounts.", None

        from_account = get_caas_account(user_id=user_id, account_id=from_account_id)
        to_account = get_caas_account(user_id=user_id, account_id=to_account_id)
        if not from_account or not to_account:
            return "One or both accounts were not found.", None
        if from_account.get("status") != "active" or to_account.get("status") != "active":
            return "Both accounts must be active.", None
        if from_account.get("currency") != currency or to_account.get("currency") != currency:
            return "Currency mismatch for transfer.", None

        available = Decimal(str(from_account.get("balance", "0")))
        if available < amount:
            return f"Insufficient funds. Available: {currency} {available}", None

        pending = {
            "intent": intent,
            "params": {
                "from_account_id": from_account_id,
                "to_account_id": to_account_id,
                "amount": str(amount),
                "currency": currency,
            },
        }
        summary = (
            f"Transfer {currency} {amount} from {from_account_id} to {to_account_id}."
        )
        return _build_confirm_message(summary), pending

    if intent == "open_account":
        account_type = str(params.get("account_type", "checking")).lower().strip() or "checking"
        currency = str(params.get("currency", "USD")).upper().strip() or "USD"
        pending = {"intent": intent, "params": {"account_type": account_type, "currency": currency}}
        summary = f"Open a new {currency} {account_type} account."
        return _build_confirm_message(summary), pending

    if intent == "close_account":
        account_id = str(params.get("account_id", "")).strip()
        if not account_id:
            return "Close account requires account_id.", None

        account = get_caas_account(user_id=user_id, account_id=account_id)
        if not account:
            return "Account not found.", None
        if Decimal(str(account.get("balance", "0"))) > Decimal("0"):
            return "Account closure denied. Balance must be zero.", None

        pending = {"intent": intent, "params": {"account_id": account_id}}
        summary = f"Close account {account_id}."
        return _build_confirm_message(summary), pending

    if intent == "open_card":
        linked_account_id = str(params.get("linked_account_id", "")).strip()
        card_type = str(params.get("card_type", "debit")).lower().strip() or "debit"
        if not linked_account_id:
            return "Open card requires linked_account_id.", None

        account = get_caas_account(user_id=user_id, account_id=linked_account_id)
        if not account:
            return "Linked account not found.", None
        if account.get("status") != "active":
            return "Linked account is not active.", None

        pending = {"intent": intent, "params": {"linked_account_id": linked_account_id, "card_type": card_type}}
        summary = f"Open {card_type} card linked to account {linked_account_id}."
        return _build_confirm_message(summary), pending

    if intent == "close_card":
        card_id = str(params.get("card_id", "")).strip()
        if not card_id:
            return "Close card requires card_id.", None

        card = get_caas_card(user_id=user_id, card_id=card_id)
        if not card:
            return "Card not found.", None
        if card.get("status") in {"closed", "expired"}:
            return "Card is already closed/expired.", None

        expires_at = card.get("expires_at")
        if expires_at:
            try:
                if date.fromisoformat(str(expires_at)) < date.today():
                    return "Card is expired and cannot be actively closed.", None
            except ValueError:
                pass

        pending = {"intent": intent, "params": {"card_id": card_id}}
        summary = f"Close card {card_id}."
        return _build_confirm_message(summary), pending

    return "No transaction action recognized. I can still help with banking questions.", None
