-- 004_create_financial_rls.sql
-- Run after 003.

alter table public.caas_accounts enable row level security;
alter table public.caas_cards enable row level security;
alter table public.caas_transactions enable row level security;

drop policy if exists caas_service_role_full_access_accounts on public.caas_accounts;
create policy caas_service_role_full_access_accounts
on public.caas_accounts
for all
using (auth.role() = 'service_role')
with check (auth.role() = 'service_role');

drop policy if exists caas_service_role_full_access_cards on public.caas_cards;
create policy caas_service_role_full_access_cards
on public.caas_cards
for all
using (auth.role() = 'service_role')
with check (auth.role() = 'service_role');

drop policy if exists caas_service_role_full_access_transactions on public.caas_transactions;
create policy caas_service_role_full_access_transactions
on public.caas_transactions
for all
using (auth.role() = 'service_role')
with check (auth.role() = 'service_role');
