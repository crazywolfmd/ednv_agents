-- 002_create_rls.sql
-- Optional: Run after table creation.
-- This enables RLS and grants access only to service_role by default.

alter table public.caas_users enable row level security;
alter table public.caas_chat_messages enable row level security;
alter table public.caas_user_access_logs enable row level security;

drop policy if exists caas_service_role_full_access_users on public.caas_users;
create policy caas_service_role_full_access_users
on public.caas_users
for all
using (auth.role() = 'service_role')
with check (auth.role() = 'service_role');

drop policy if exists caas_service_role_full_access_chat_messages on public.caas_chat_messages;
create policy caas_service_role_full_access_chat_messages
on public.caas_chat_messages
for all
using (auth.role() = 'service_role')
with check (auth.role() = 'service_role');

drop policy if exists caas_service_role_full_access_user_access_logs on public.caas_user_access_logs;
create policy caas_service_role_full_access_user_access_logs
on public.caas_user_access_logs
for all
using (auth.role() = 'service_role')
with check (auth.role() = 'service_role');
