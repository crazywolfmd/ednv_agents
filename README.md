# Chaos-as-a-service

Minimal AI Agents starter project with:
- `LangChain` for orchestration
- `LangGraph` for workflow/state
- `LangSmith` for tracing
- `Streamlit` frontend with auth-gated chat
- `Supabase` for auth/data tables

## Project layout

```text
.
|-- app.py                         # Root Streamlit entrypoint
|-- requirements.txt
|-- .env.example
|-- .streamlit
|   `-- config.toml                # Hides technical error details in UI
|-- streamlit_app
|   |-- app.py                     # Main Streamlit runtime/router
|   |-- settings.py
|   |-- auth
|   |   |-- service.py             # caas_users authentication/session helpers
|   |   `-- ui.py                  # Login screen
|   `-- pages
|       `-- system_status.py
|-- agents
|   |-- settings.py
|   |-- chains.py
|   |-- graph.py
|   `-- main.py
`-- db
    |-- client.py                  # Supabase client config
    `-- repository.py
```

## Quickstart (Windows PowerShell)

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```

Set values in `.env`:

```env
OPENAI_API_KEY=...
OPENAI_MODEL=gpt-4o-mini
LANGSMITH_API_KEY=...          # optional
LANGSMITH_TRACING=true
LANGSMITH_PROJECT=chaos-as-a-service-dev
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_ANON_KEY=...
```

## Run

Streamlit app:

```powershell
streamlit run app.py
```

CLI mode:

```powershell
python -m agents.main
```

## Auth flow (`caas_users`)

- Login checks `caas_users` directly by identifier (`email` first, then `username`) and verifies `password_hash` with bcrypt.
- App expects `caas_users` columns: `user_id`, `username`, `name`, `lastname`, `email`, `password_hash`.
- Successful login stores only user profile fields in Streamlit session state.

## User-facing error behavior

- App catches runtime exceptions and shows friendly messages.
- Technical stack traces are hidden in UI via `.streamlit/config.toml`.
