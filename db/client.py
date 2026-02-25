from __future__ import annotations

import os
from typing import Any

from dotenv import load_dotenv


load_dotenv()


def _get_secret(name: str) -> str | None:
    value = os.getenv(name)
    if value:
        return value

    try:
        import streamlit as st

        if name in st.secrets:
            return st.secrets[name]
    except Exception:
        return None

    return None


def get_supabase_config() -> dict[str, str | None]:
    return {
        "url": _get_secret("SUPABASE_URL"),
        "key": _get_secret("SUPABASE_ANON_KEY") or _get_secret("SUPABASE_KEY"),
    }


def create_supabase_client() -> Any:
    config = get_supabase_config()
    if not config["url"] or not config["key"]:
        raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY/SUPABASE_KEY are required.")

    from supabase import create_client

    return create_client(config["url"], config["key"])
