-- 006_seed_test_user_financial_data.sql
-- Seeds deterministic dummy financial data for username 'test'.
-- Safe to rerun: seeded transactions are replaced, accounts/cards are upserted by fixed IDs.

-- Accounts for test user
with test_user as (
  select user_id
  from public.caas_users
  where username = 'test'
  limit 1
)
insert into public.caas_accounts (
  account_id,
  user_id,
  account_type,
  currency,
  balance,
  status,
  opened_at,
  closed_at
)
select
  v.account_id,
  tu.user_id,
  v.account_type,
  v.currency,
  v.balance,
  v.status,
  v.opened_at,
  v.closed_at
from test_user tu
cross join (
  values
    ('11111111-1111-1111-1111-111111111111'::uuid, 'checking'::text, 'USD'::text, 1250.75::numeric, 'active'::text, now() - interval '90 days', null::timestamptz),
    ('22222222-2222-2222-2222-222222222222'::uuid, 'savings'::text, 'USD'::text, 5400.00::numeric, 'active'::text, now() - interval '120 days', null::timestamptz),
    ('33333333-3333-3333-3333-333333333333'::uuid, 'checking'::text, 'EUR'::text, 80.00::numeric, 'blocked'::text, now() - interval '150 days', null::timestamptz)
) as v(account_id, account_type, currency, balance, status, opened_at, closed_at)
on conflict (account_id) do update
set
  user_id = excluded.user_id,
  account_type = excluded.account_type,
  currency = excluded.currency,
  balance = excluded.balance,
  status = excluded.status,
  opened_at = excluded.opened_at,
  closed_at = excluded.closed_at,
  updated_at = now();

-- Cards for test user
with test_user as (
  select user_id
  from public.caas_users
  where username = 'test'
  limit 1
)
insert into public.caas_cards (
  card_id,
  user_id,
  linked_account_id,
  card_type,
  status,
  expires_at,
  opened_at,
  closed_at
)
select
  v.card_id,
  tu.user_id,
  v.linked_account_id,
  v.card_type,
  v.status,
  v.expires_at,
  v.opened_at,
  v.closed_at
from test_user tu
cross join (
  values
    ('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'::uuid, '11111111-1111-1111-1111-111111111111'::uuid, 'debit'::text, 'active'::text, (current_date + 365), now() - interval '80 days', null::timestamptz),
    ('bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb'::uuid, '22222222-2222-2222-2222-222222222222'::uuid, 'virtual'::text, 'active'::text, (current_date + 120), now() - interval '45 days', null::timestamptz),
    ('cccccccc-cccc-cccc-cccc-cccccccccccc'::uuid, '33333333-3333-3333-3333-333333333333'::uuid, 'debit'::text, 'expired'::text, (current_date - 10), now() - interval '400 days', now() - interval '5 days')
) as v(card_id, linked_account_id, card_type, status, expires_at, opened_at, closed_at)
on conflict (card_id) do update
set
  user_id = excluded.user_id,
  linked_account_id = excluded.linked_account_id,
  card_type = excluded.card_type,
  status = excluded.status,
  expires_at = excluded.expires_at,
  opened_at = excluded.opened_at,
  closed_at = excluded.closed_at,
  updated_at = now();

-- Replace only seeded transactions for test user
with test_user as (
  select user_id
  from public.caas_users
  where username = 'test'
  limit 1
)
delete from public.caas_transactions t
where t.user_id = (select user_id from test_user)
  and coalesce(t.metadata ->> 'seed', '') = 'true';

-- Seed transactions for test user
with test_user as (
  select user_id
  from public.caas_users
  where username = 'test'
  limit 1
)
insert into public.caas_transactions (
  user_id,
  tx_type,
  from_account_id,
  to_account_id,
  amount,
  currency,
  status,
  reason,
  metadata,
  created_at
)
select
  tu.user_id,
  v.tx_type,
  v.from_account_id,
  v.to_account_id,
  v.amount,
  v.currency,
  v.status,
  v.reason,
  v.metadata,
  v.created_at
from test_user tu
cross join (
  values
    ('internal_transfer'::text, '11111111-1111-1111-1111-111111111111'::uuid, '22222222-2222-2222-2222-222222222222'::uuid, 75.25::numeric, 'USD'::text, 'approved'::text, 'Monthly savings transfer'::text, '{"seed":"true","seed_key":"tx_1"}'::jsonb, now() - interval '3 days'),
    ('card_open'::text, null::uuid, null::uuid, null::numeric, null::text, 'approved'::text, 'Virtual card created'::text, '{"seed":"true","seed_key":"tx_2","card_id":"bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"}'::jsonb, now() - interval '20 days'),
    ('account_open'::text, null::uuid, null::uuid, null::numeric, null::text, 'approved'::text, 'Savings account created'::text, '{"seed":"true","seed_key":"tx_3","account_id":"22222222-2222-2222-2222-222222222222"}'::jsonb, now() - interval '120 days')
) as v(tx_type, from_account_id, to_account_id, amount, currency, status, reason, metadata, created_at);

-- Optional verification
select
  'seed_complete' as status,
  (select count(*) from public.caas_accounts a where a.user_id = (select user_id from public.caas_users where username = 'test' limit 1)) as account_count,
  (select count(*) from public.caas_cards c where c.user_id = (select user_id from public.caas_users where username = 'test' limit 1)) as card_count,
  (select count(*) from public.caas_transactions t where t.user_id = (select user_id from public.caas_users where username = 'test' limit 1)) as transaction_count;
