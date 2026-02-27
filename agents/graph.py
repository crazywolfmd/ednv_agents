from __future__ import annotations

import json
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph
from langsmith import traceable

from agents.chains import build_chat_chain, build_task_chain, build_validation_chain
from agents.rules_engine import handle_rules_and_execution


class AgentState(TypedDict, total=False):
    user_input: str
    user_id: str
    pending_action: dict[str, Any] | None
    intent: str
    action_params: dict[str, Any]
    assistant_response: str
    token_usage: dict[str, Any]


def _safe_json_loads(payload: str) -> dict[str, Any]:
    try:
        return json.loads(payload)
    except Exception:
        return {}


def _extract_usage(message: Any) -> dict[str, Any]:
    prompt_tokens = 0
    completion_tokens = 0
    total_tokens = 0
    llm_model = ""

    usage_metadata = getattr(message, "usage_metadata", None)
    if isinstance(usage_metadata, dict):
        prompt_tokens = int(usage_metadata.get("input_tokens", 0) or 0)
        completion_tokens = int(usage_metadata.get("output_tokens", 0) or 0)
        total_tokens = int(usage_metadata.get("total_tokens", 0) or 0)

    response_metadata = getattr(message, "response_metadata", None)
    if isinstance(response_metadata, dict):
        token_usage = response_metadata.get("token_usage", {})
        if isinstance(token_usage, dict):
            prompt_tokens = int(token_usage.get("prompt_tokens", prompt_tokens) or prompt_tokens)
            completion_tokens = int(token_usage.get("completion_tokens", completion_tokens) or completion_tokens)
            total_tokens = int(token_usage.get("total_tokens", total_tokens) or total_tokens)

        llm_model = str(response_metadata.get("model_name") or response_metadata.get("model") or "")

    if total_tokens == 0:
        total_tokens = prompt_tokens + completion_tokens

    return {
        "prompt_tokens": max(prompt_tokens, 0),
        "completion_tokens": max(completion_tokens, 0),
        "total_tokens": max(total_tokens, 0),
        "llm_calls": 1,
        "llm_model": llm_model,
    }


def _merge_usage(base: dict[str, Any] | None, inc: dict[str, Any] | None) -> dict[str, Any]:
    base = base or {}
    inc = inc or {}

    prompt_tokens = int(base.get("prompt_tokens", 0) or 0) + int(inc.get("prompt_tokens", 0) or 0)
    completion_tokens = int(base.get("completion_tokens", 0) or 0) + int(inc.get("completion_tokens", 0) or 0)
    total_tokens = int(base.get("total_tokens", 0) or 0) + int(inc.get("total_tokens", 0) or 0)
    llm_calls = int(base.get("llm_calls", 0) or 0) + int(inc.get("llm_calls", 0) or 0)
    llm_model = str(inc.get("llm_model") or base.get("llm_model") or "")

    return {
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
        "llm_calls": llm_calls,
        "llm_model": llm_model,
    }


def _normalize_for_match(text: str) -> str:
    cleaned = " ".join(str(text or "").strip().lower().split())
    for ch in "?!.,;:\"'":
        cleaned = cleaned.replace(ch, "")
    return cleaned


def _override_intent_from_text(user_input: str, predicted_intent: str) -> str:
    text = _normalize_for_match(user_input)

    account_phrases = {
        "list accounts",
        "show accounts",
        "show my accounts",
        "show my balances",
        "how many accounts do i have",
        "what accounts do i have",
        "what is my balance",
        "what are my balances",
    }

    if text in account_phrases:
        return "check_balance"

    if "account" in text and "how many" in text:
        return "check_balance"

    if "balance" in text and "transaction" not in text:
        return "check_balance"

    return predicted_intent


@traceable(name="task_agent")
def task_agent(state: AgentState) -> AgentState:
    user_input = state.get("user_input", "")
    normalized = user_input.strip().upper()
    usage = state.get("token_usage", {})

    if normalized in {"CONFIRM", "CANCEL"}:
        return {
            "intent": "transaction_control",
            "action_params": {},
            "token_usage": usage,
        }

    chain = build_task_chain()
    output = chain.invoke({"user_input": user_input})
    usage = _merge_usage(usage, _extract_usage(output))
    raw = getattr(output, "content", "") or ""
    parsed = _safe_json_loads(raw)

    intent = _override_intent_from_text(user_input, str(parsed.get("intent", "general_chat")))
    action_params = parsed.get("params", {}) if isinstance(parsed.get("params"), dict) else {}
    general_response = str(parsed.get("general_response", "")).strip()

    result: AgentState = {
        "intent": intent,
        "action_params": action_params,
        "token_usage": usage,
    }

    if intent == "general_chat":
        if general_response:
            result["assistant_response"] = general_response
        else:
            chat_chain = build_chat_chain()
            chat_output = chat_chain.invoke({"user_input": user_input})
            result["assistant_response"] = getattr(chat_output, "content", "") or ""
            result["token_usage"] = _merge_usage(usage, _extract_usage(chat_output))

    return result


@traceable(name="rules_engine")
def rules_engine(state: AgentState) -> AgentState:
    intent = state.get("intent", "general_chat")
    if intent == "general_chat":
        return {}

    response, pending = handle_rules_and_execution(
        user_id=str(state.get("user_id", "")),
        user_input=state.get("user_input", ""),
        intent=intent,
        params=state.get("action_params", {}) or {},
        pending_action=state.get("pending_action"),
    )
    return {
        "assistant_response": response,
        "pending_action": pending,
    }


@traceable(name="validator_agent")
def validator_agent(state: AgentState) -> AgentState:
    response = state.get("assistant_response", "")
    usage = state.get("token_usage", {})
    intent = str(state.get("intent", "general_chat"))

    if intent != "general_chat":
        return {"assistant_response": response, "token_usage": usage}

    if not response:
        return {
            "assistant_response": "I could not generate a response right now.",
            "token_usage": usage,
        }

    chain = build_validation_chain()
    output = chain.invoke({"assistant_response": response})
    usage = _merge_usage(usage, _extract_usage(output))
    parsed = _safe_json_loads(getattr(output, "content", "") or "")
    final_response = str(parsed.get("final_response", "")).strip()

    if final_response:
        return {"assistant_response": final_response, "token_usage": usage}
    return {"assistant_response": response, "token_usage": usage}


def build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("task_agent", task_agent)
    graph.add_node("rules_engine", rules_engine)
    graph.add_node("validator_agent", validator_agent)
    graph.add_edge(START, "task_agent")
    graph.add_edge("task_agent", "rules_engine")
    graph.add_edge("rules_engine", "validator_agent")
    graph.add_edge("validator_agent", END)
    return graph.compile()


