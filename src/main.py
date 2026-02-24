from __future__ import annotations

from src.graph import build_graph


def main():
    graph = build_graph()
    user_input = input("Prompt: ").strip()
    if not user_input:
        print("No input provided.")
        return
    result = graph.invoke({"user_input": user_input, "response": ""})
    print(result["response"])


if __name__ == "__main__":
    main()
