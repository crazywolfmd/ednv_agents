from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Settings:
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    langsmith_project: str = os.getenv("LANGSMITH_PROJECT", "endv-agents-dev")


settings = Settings()
