# ednv_agents

Minimal AI Agents starter project with:
- `LangChain` for model orchestration
- `LangGraph` for agent workflow/state graph
- `LangSmith` for tracing and observability
- `Streamlit` for a lightweight frontend

## Goal

This repository is a clean starting point for building and iterating on small agent workflows.
Current implementation is intentionally minimal: one graph node that calls an LLM and returns a response.

## Project layout

```text
.
|-- app.py                # Streamlit UI
|-- requirements.txt      # Python dependencies
|-- .env.example          # Environment variable template
`-- src
    |-- __init__.py
    |-- settings.py       # App/runtime settings
    |-- chains.py         # LangChain model + prompt pipeline
    |-- graph.py          # LangGraph state + compiled graph
    `-- main.py           # CLI entrypoint for quick local testing
```

## Quickstart (Windows PowerShell)

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Then set values in `.env`:

```env
OPENAI_API_KEY=...
OPENAI_MODEL=gpt-4o-mini
LANGSMITH_API_KEY=...          # optional but recommended
LANGSMITH_TRACING=true
LANGSMITH_PROJECT=ednv-agents-dev
```

## Run

Streamlit app:

```powershell
streamlit run app.py
```

CLI mode:

```powershell
python -m src.main
```

## Notes

- LangSmith tracing activates when `LANGSMITH_API_KEY` is set and tracing is enabled.
- This is a starter scaffold; extend `src/graph.py` with more nodes/tools as your first iteration.
