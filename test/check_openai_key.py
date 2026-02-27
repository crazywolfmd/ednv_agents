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
        return "Bad request: model name may be invalid/inaccessible or payload is rejected."
    if isinstance(exc, APITimeoutError):
        return "Request timed out."
    if isinstance(exc, APIConnectionError):
        return "Connection failed (network/DNS/TLS issue)."
    if isinstance(exc, APIStatusError):
        return f"API returned HTTP {exc.status_code}."
    return f"Unexpected error: {exc}"


def test_responses(client: OpenAI, model: str) -> bool:
    _print_header("Responses API (/v1/responses)")
    try:
        response = client.responses.create(
            model=model,
            input="Reply with exactly: pong",
            max_output_tokens=16,
        )
        text = (response.output_text or "").strip()
        usage = getattr(response, "usage", None)
        _print_ok(f"Call succeeded. Output: {text!r}")
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


def test_chat_completions(client: OpenAI, model: str) -> bool:
    _print_header("Chat Completions API (/v1/chat/completions)")
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "Reply with exactly: pong"}],
            max_tokens=16,
        )
        text = (response.choices[0].message.content or "").strip()
        usage = response.usage
        _print_ok(f"Call succeeded. Output: {text!r}")
        if usage:
            _print_ok(
                "Usage: "
                f"prompt_tokens={getattr(usage, 'prompt_tokens', 'n/a')}, "
                f"completion_tokens={getattr(usage, 'completion_tokens', 'n/a')}, "
                f"total_tokens={getattr(usage, 'total_tokens', 'n/a')}"
            )
        return True
    except Exception as exc:  # noqa: BLE001
        _print_fail(_summarize_error(exc))
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Check OpenAI key/model access and restrictions.")
    parser.add_argument(
        "--model",
        default=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        help="Model to test (default: OPENAI_MODEL or gpt-4o-mini).",
    )
    parser.add_argument(
        "--mode",
        choices=["responses", "chat", "both"],
        default="both",
        help="Endpoint(s) to test.",
    )
    args = parser.parse_args()

    load_dotenv()

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        _print_fail("OPENAI_API_KEY is missing (not found in environment variables or repo-root .env).")
        return 2

    _print_header("Configuration")
    _print_ok(f"Model: {args.model}")
    _print_ok(f"Mode: {args.mode}")
    _print_ok(f"Key prefix: {api_key[:10]}...")

    client = OpenAI(api_key=api_key)

    results: list[bool] = []
    if args.mode in {"responses", "both"}:
        results.append(test_responses(client, args.model))
    if args.mode in {"chat", "both"}:
        results.append(test_chat_completions(client, args.model))

    _print_header("Summary")
    passed = sum(1 for ok in results if ok)
    total = len(results)
    print(f"Passed {passed}/{total} checks.")

    if passed == total:
        _print_ok("OpenAI key/model look good for tested endpoint(s).")
        return 0

    _print_fail("At least one endpoint failed. Review messages above for exact reason.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
