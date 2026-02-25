from __future__ import annotations

from agents.graph import build_graph


def main():
    graph = build_graph()
    user_input = input("Prompt: ").strip()
    if not user_input:
        print("No input provided.")
        return
    result = graph.invoke(
        {
            "user_input": user_input,
            "user_id": "cli-user",
            "pending_action": None,
            "assistant_response": "",
        }
    )
    print(result.get("assistant_response", ""))


if __name__ == "__main__":
    main()
