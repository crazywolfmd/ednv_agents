# DB SQL Setup

Run scripts in order in Supabase SQL Editor:

1. `db/sql/001_create_tables.sql`
2. `db/sql/002_create_rls.sql`
3. `db/sql/003_create_financial_tables.sql`
4. `db/sql/004_create_financial_rls.sql`
5. `db/sql/005_add_llm_token_usage_columns.sql`
6. `db/sql/006_seed_test_user_financial_data.sql` (optional seed for username `test`)
7. `db/sql/007_add_access_role_to_users.sql`
8. `db/sql/008_assign_initial_user_roles.sql`
9. `db/sql/009_add_llm_observability_columns.sql`
10. `db/sql/010_backfill_llm_provider.sql` (optional backfill)
11. `db/sql/011_create_admin_analytics_views.sql` 
12. `db/sql/012_backfill_llm_provider_by_model.sql` (optional backfill for mixed providers)

Notes:
- All project tables use the `caas_` prefix.
- `caas_users.password_hash` stores bcrypt hashes.
- `caas_users.access_role` supports `admin` and `user`.
- `caas_user_access_logs` stores login/logout audit events.
- Financial operations use `caas_accounts`, `caas_cards`, `caas_transactions`.
- `caas_chat_messages` stores per-turn token usage metadata (`llm_*` columns).
- Admin dashboard queries analytics views `caas_admin_vw_*` from `011_create_admin_analytics_views.sql`.
- Login lookup uses `email` first, then `username`.


