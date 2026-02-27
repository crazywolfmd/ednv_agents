# Chaos-as-a-service

AI agent banking sandbox with Streamlit frontend, LangGraph orchestration, and Supabase persistence.

## Features

- Username/email login against `caas_users` with bcrypt hashes.
- Role-aware UI (`admin` and `user`) via `access_role` (baseline assignment in SQL script `008_add_access_role_to_users.sql`: `caas_admin` -> `admin`, `test` -> `user`).
- Streamlit multipage app:
  - Chat
  - Password Generator
  - System Status
  - Admin Console (admin only)
- LangGraph pipeline:
  - `task_agent`: intent + params extraction
  - `rules_engine`: deterministic banking logic + guardrails
  - `validator_agent`: final user-facing response polishing
- Banking operations:
  - check balances / list accounts
  - list recent transactions
  - internal transfer between own accounts
  - open/close account
  - open/close card
- Confirmation flow for transactional actions (`CONFIRM` / `CANCEL`).
- Multi-turn parameter collection (implemented for `open_card` when `linked_account_id` is missing).
- Chat persistence in `caas_chat_messages` with daily cleanup.
- User access audit logging in `caas_user_access_logs`.
- LLM observability:
  - provider/model
  - prompt/completion/total tokens
  - llm calls
- Admin analytics dashboard powered by SQL views (`caas_admin_vw_*`):
  - KPI cards
  - usage trends
  - provider/model usage
  - transaction analytics
  - auth events
  - entity status and data quality checks
- Wide layout + chat label timestamps (`You (HH:MM:SS)`, `Assistant (HH:MM:SS)`).

## Project layout

```text
.
|-- app.py
|-- streamlit_app/
|   |-- app.py
|   |-- auth/
|   `-- pages/
|-- agents/
|-- db/
|   |-- repository.py
|   `-- sql/
|-- generator/
|-- test/
|-- requirements.txt
`-- README.md
```

## Setup

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```

## Environment variables

### LLM provider selection

#### OpenAI

```env
LLM_PROVIDER=openai
OPENAI_API_KEY=...
OPENAI_MODEL=gpt-5-nano
# OPENAI_BASE_URL=https://api.openai.com/v1
LLM_TEMPERATURE=0
```

#### Hugging Face (OpenAI-compatible endpoint)

```env
LLM_PROVIDER=huggingface
HUGGINGFACE_API_KEY=...
HUGGINGFACE_MODEL=meta-llama/Llama-3.1-8B-Instruct
HUGGINGFACE_BASE_URL=https://router.huggingface.co/v1
LLM_TEMPERATURE=0
```

### Other config

```env
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_KEY=your_service_role_key

LANGSMITH_TRACING=true
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
LANGSMITH_API_KEY=...            # optional
LANGSMITH_PROJECT=chaos-as-a-service-dev
```

## Database migrations (order)

Run in Supabase SQL Editor:

1. `db/sql/001_create_tables.sql`
2. `db/sql/002_create_rls.sql`
3. `db/sql/003_create_financial_tables.sql`
4. `db/sql/004_create_financial_rls.sql`
5. `db/sql/005_add_llm_token_usage_columns.sql`
6. `db/sql/006_seed_test_user_financial_data.sql` (optional)
7. `db/sql/007_create_admin_analytics_views.sql`
8. `db/sql/008_add_access_role_to_users.sql`
9. `db/sql/009_add_llm_observability_columns.sql`
10. `db/sql/010_backfill_llm_provider.sql` (optional)

## Run

```powershell
streamlit run app.py
```

## Transaction behavior notes

- Transactional actions are staged and require explicit confirmation.
- Type `CONFIRM` to execute and `CANCEL` to abort.
- For `open_card`, if `linked_account_id` is missing, the app asks for it and continues in the next message.

## Tests / diagnostics

```powershell
python test/check_llm_provider.py --provider openai
python test/check_llm_provider.py --provider huggingface
python test/check_openai_key.py
```
