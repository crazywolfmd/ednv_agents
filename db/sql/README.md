# DB SQL Setup

Run scripts in order in Supabase SQL Editor:

1. `db/sql/001_create_tables.sql`
2. `db/sql/002_create_rls.sql` (optional, for service-role access)

Notes:
- All project tables use the `caas_` prefix.
- `caas_users.password_hash` stores bcrypt hashes.
- Insert your test users manually.
- Login lookup uses `email` first, then `username`.
