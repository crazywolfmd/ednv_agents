from __future__ import annotations

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from agents.settings import settings


TASK_SYSTEM_PROMPT = """
You are a banking task agent. Extract a structured intent from user input.
Return valid JSON only using this schema:
{
  "intent": "general_chat|check_balance|list_recent_transactions|transfer_between_accounts|open_account|close_account|open_card|close_card",
  "params": {
    "account_id": "optional uuid/string",
    "from_account_id": "optional uuid/string",
    "to_account_id": "optional uuid/string",
    "amount": "optional number",
    "currency": "optional currency code",
    "account_type": "optional checking|savings",
    "linked_account_id": "optional uuid/string",
    "card_type": "optional debit|virtual",
    "card_id": "optional uuid/string"
  },
  "general_response": "use only for general_chat, otherwise empty"
}
Rules:
- If the user writes CONFIRM or CANCEL, set intent to general_chat and keep params empty.
- For non-transactional conversation, set intent to general_chat with a concise helpful answer in general_response.
""".strip()

VALIDATION_SYSTEM_PROMPT = """
You are a banking response validator.
Ensure final user text is clear, non-technical, and does not expose internal system details.
Return JSON only:
{
  "approved": true,
  "final_response": "final message for end user"
}
""".strip()


def _build_openai_llm() -> ChatOpenAI:
    kwargs: dict[str, object] = {
        "model": settings.openai_model,
        "temperature": settings.llm_temperature,
    }
    if settings.openai_base_url:
        kwargs["base_url"] = settings.openai_base_url
    return ChatOpenAI(**kwargs)


def _build_huggingface_llm() -> ChatOpenAI:
    if not settings.huggingface_api_key:
        raise ValueError("HUGGINGFACE_API_KEY (or HF_TOKEN) is required when LLM_PROVIDER=huggingface")

    return ChatOpenAI(
        model=settings.huggingface_model,
        api_key=settings.huggingface_api_key,
        base_url=settings.huggingface_base_url,
        temperature=settings.llm_temperature,
    )


def _build_llm() -> ChatOpenAI:
    if settings.llm_provider == "openai":
        return _build_openai_llm()
    if settings.llm_provider == "huggingface":
        return _build_huggingface_llm()
    raise ValueError("Unsupported LLM_PROVIDER. Use 'openai' or 'huggingface'.")


def build_task_chain():
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", TASK_SYSTEM_PROMPT),
            ("human", "{user_input}"),
        ]
    )
    return prompt | _build_llm()


def build_validation_chain():
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", VALIDATION_SYSTEM_PROMPT),
            ("human", "{assistant_response}"),
        ]
    )
    return prompt | _build_llm()


def build_chat_chain():
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are a concise retail banking assistant. Give practical, clear guidance.",
            ),
            ("human", "{user_input}"),
        ]
    )
    return prompt | _build_llm()
