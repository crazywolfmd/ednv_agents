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

Set `.env` (or Streamlit Secrets):

```env
OPENAI_API_KEY=...
OPENAI_MODEL=gpt-4o-mini
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

## Run

```powershell
streamlit run app.py
```

## Transaction usage notes

- Transfer/open/close actions require explicit confirmation.
- When prompted, type `CONFIRM` to execute or `CANCEL` to abort.

Example prompts:
- `Show my balances`
- `Transfer 25 USD from <from_account_id> to <to_account_id>`
- `Open a USD savings account`
- `Open a virtual card linked to <account_id>`
- `Close card <card_id>`
