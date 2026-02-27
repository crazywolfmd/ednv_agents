# Chaos-as-a-service

AI agent banking sandbox with Streamlit frontend, LangGraph orchestration, and Supabase persistence.

## What it does

- Auth against `caas_users` (bcrypt password hashes)
- Chat assistant with two-agent flow:
  - `task_agent` for intent + parameter extraction
  - `validator_agent` for user-facing response cleanup
- Deterministic financial rules/execution layer for:
  - check balances
  - list recent transactions
  - internal transfer between own accounts
  - open/close account
  - open/close card
- Login/access audit logging in `caas_user_access_logs`

## Project layout

```text
.
|-- app.py
|-- streamlit_app/
|-- agents/
|-- db/
|   `-- sql/
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

## LLM provider config

Switch provider only by env values.

### OpenAI

```env
LLM_PROVIDER=openai
OPENAI_API_KEY=...
OPENAI_MODEL=gpt-5-nano
# OPENAI_BASE_URL=https://api.openai.com/v1
LLM_TEMPERATURE=0
```

### Hugging Face (OpenAI-compatible endpoint)

```env
LLM_PROVIDER=huggingface
HUGGINGFACE_API_KEY=...
HUGGINGFACE_MODEL=meta-llama/Llama-3.1-8B-Instruct
HUGGINGFACE_BASE_URL=https://router.huggingface.co/v1
LLM_TEMPERATURE=0
```

## Other required config

```env
LANGSMITH_API_KEY=...              # optional
LANGSMITH_TRACING=true
LANGSMITH_PROJECT=chaos-as-a-service-dev
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_KEY=your_service_role_key
```

## Database migration order

Run in Supabase SQL Editor:

1. `db/sql/001_create_tables.sql`
2. `db/sql/002_create_rls.sql`
3. `db/sql/003_create_financial_tables.sql`
4. `db/sql/004_create_financial_rls.sql`
5. `db/sql/005_add_llm_token_usage_columns.sql`
6. `db/sql/006_seed_test_user_financial_data.sql` (optional)
7. `db/sql/007_add_access_role_to_users.sql`

## Run

```powershell
streamlit run app.py
```

## Transaction usage notes

- Transfer/open/close actions require explicit confirmation.
- When prompted, type `CONFIRM` to execute or `CANCEL` to abort.


## Test LLM provider

```powershell
python test/check_llm_provider.py --provider openai
python test/check_llm_provider.py --provider huggingface
```