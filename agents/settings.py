import os
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv


load_dotenv()


def _get_secret(name: str) -> Optional[str]:
    value = os.getenv(name)
    if value:
        return value.strip()

    try:
        import streamlit as st

        if name in st.secrets:
            return str(st.secrets[name]).strip()
    except Exception:
        return None

    return None


@dataclass(frozen=True)
class AgentSettings:
    llm_provider: str = (_get_secret("LLM_PROVIDER") or "openai").lower()

    openai_model: str = _get_secret("OPENAI_MODEL") or "gpt-5-nano"
    openai_base_url: Optional[str] = _get_secret("OPENAI_BASE_URL")

    huggingface_model: str = _get_secret("HUGGINGFACE_MODEL") or "meta-llama/Llama-3.1-8B-Instruct"
    huggingface_api_key: Optional[str] = _get_secret("HUGGINGFACE_API_KEY") or _get_secret("HF_TOKEN")
    huggingface_base_url: str = _get_secret("HUGGINGFACE_BASE_URL") or "https://router.huggingface.co/v1"

    llm_temperature: float = float(_get_secret("LLM_TEMPERATURE") or "0")

    langsmith_project: str = _get_secret("LANGSMITH_PROJECT") or "chaos-as-a-service-dev"


settings = AgentSettings()
