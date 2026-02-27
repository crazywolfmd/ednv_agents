from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class AgentSettings:
    llm_provider: str = os.getenv("LLM_PROVIDER", "openai").lower()

    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-5-nano")
    openai_base_url: str | None = os.getenv("OPENAI_BASE_URL")

    huggingface_model: str = os.getenv("HUGGINGFACE_MODEL", "meta-llama/Llama-3.1-8B-Instruct")
    huggingface_api_key: str | None = os.getenv("HUGGINGFACE_API_KEY") or os.getenv("HF_TOKEN")
    huggingface_base_url: str = os.getenv("HUGGINGFACE_BASE_URL", "https://router.huggingface.co/v1")

    llm_temperature: float = float(os.getenv("LLM_TEMPERATURE", "0"))

    langsmith_project: str = os.getenv("LANGSMITH_PROJECT", "chaos-as-a-service-dev")


settings = AgentSettings()
