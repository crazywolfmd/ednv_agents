from __future__ import annotations

import argparse
import os
import sys

from dotenv import load_dotenv
from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AuthenticationError,
    BadRequestError,
    OpenAI,
    PermissionDeniedError,
    RateLimitError,
)


def _print_header(title: str) -> None:
    print(f"\n=== {title} ===")


def _print_ok(message: str) -> None:
    print(f"[OK] {message}")


def _print_fail(message: str) -> None:
    print(f"[FAIL] {message}")


def _summarize_error(exc: Exception) -> str:
    if isinstance(exc, AuthenticationError):
        return "Authentication failed: key invalid, missing, or revoked."
    if isinstance(exc, PermissionDeniedError):
        return "Permission denied: key restrictions do not allow this endpoint/model."
    if isinstance(exc, RateLimitError):
        return "Rate limit or quota exceeded."
    if isinstance(exc, BadRequestError):
        return "Bad request: model name may be invalid/inaccessible or payload was rejected."
    if isinstance(exc, APITimeoutError):
        return "Request timed out."
    if isinstance(exc, APIConnectionError):
        return "Connection failed (network/DNS/TLS issue)."
    if isinstance(exc, APIStatusError):
        return f"API returned HTTP {exc.status_code}."
    return f"Unexpected error: {exc}"


def _run_responses_check(client: OpenAI, model: str) -> bool:
    _print_header("Responses API (/v1/responses)")
    try:
        response = client.responses.create(
            model=model,
            input="Reply with exactly: pong",
            max_output_tokens=16,
        )
        text = (response.output_text or "").strip()
        _print_ok(f"Call succeeded. Output: {text!r}")
        usage = getattr(response, "usage", None)
        if usage:
            _print_ok(
                "Usage: "
                f"input_tokens={getattr(usage, 'input_tokens', 'n/a')}, "
                f"output_tokens={getattr(usage, 'output_tokens', 'n/a')}, "
                f"total_tokens={getattr(usage, 'total_tokens', 'n/a')}"
            )
        return True
    except Exception as exc:  # noqa: BLE001
        _print_fail(_summarize_error(exc))
        return False


def _build_provider_client(provider: str) -> tuple[OpenAI | None, str | None, str]:
    provider = provider.lower()

    if provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        model = os.getenv("OPENAI_MODEL", "gpt-5-nano")
        base_url = os.getenv("OPENAI_BASE_URL")
        if not api_key:
            return None, None, "OPENAI_API_KEY is missing."
        client = OpenAI(api_key=api_key, base_url=base_url) if base_url else OpenAI(api_key=api_key)
        return client, model, ""

    if provider == "huggingface":
        api_key = os.getenv("HUGGINGFACE_API_KEY") or os.getenv("HF_TOKEN")
        model = os.getenv("HUGGINGFACE_MODEL", "meta-llama/Llama-3.1-8B-Instruct")
        base_url = os.getenv("HUGGINGFACE_BASE_URL", "https://router.huggingface.co/v1")
        if not api_key:
            return None, None, "HUGGINGFACE_API_KEY (or HF_TOKEN) is missing."
        client = OpenAI(api_key=api_key, base_url=base_url)
        return client, model, ""

    return None, None, "Unsupported LLM_PROVIDER. Use 'openai' or 'huggingface'."


def main() -> int:
    parser = argparse.ArgumentParser(description="Check currently selected LLM provider from .env/env vars.")
    parser.add_argument(
        "--provider",
        default=os.getenv("LLM_PROVIDER", "openai"),
        choices=["openai", "huggingface"],
        help="Provider to test (default: LLM_PROVIDER env).",
    )
    args = parser.parse_args()

    load_dotenv()

    _print_header("Configuration")
    _print_ok(f"LLM_PROVIDER={args.provider}")

    client, model, error = _build_provider_client(args.provider)
    if error:
        _print_fail(error)
        return 2

    _print_ok(f"Model={model}")

    ok = _run_responses_check(client, model)

    _print_header("Summary")
    if ok:
        _print_ok("Provider/model configuration is working for Responses API.")
        return 0

    _print_fail("Provider check failed. Review error details above.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
