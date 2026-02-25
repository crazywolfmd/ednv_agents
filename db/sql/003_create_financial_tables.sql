-- 003_create_financial_tables.sql
-- Run after 001/002 to enable transaction-style agent operations.

create table if not exists public.caas_accounts (
  account_id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.caas_users(user_id) on delete cascade,
  account_type text not null check (account_type in ('checking', 'savings')),
  currency text not null,
  balance numeric(14,2) not null default 0,
  status text not null default 'active' check (status in ('active', 'blocked', 'closed')),
  opened_at timestamptz not null default now(),
  closed_at timestamptz,
  updated_at timestamptz not null default now()
);

create index if not exists idx_caas_accounts_user_status
  on public.caas_accounts (user_id, status);

drop trigger if exists trg_caas_accounts_updated_at on public.caas_accounts;
create trigger trg_caas_accounts_updated_at
before update on public.caas_accounts
for each row
execute function public.set_updated_at();

create table if not exists public.caas_cards (
  card_id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.caas_users(user_id) on delete cascade,
  linked_account_id uuid not null references public.caas_accounts(account_id) on delete restrict,
  card_type text not null check (card_type in ('debit', 'virtual')),
  status text not null default 'active' check (status in ('active', 'blocked', 'expired', 'closed')),
  expires_at date not null,
  opened_at timestamptz not null default now(),
  closed_at timestamptz,
  updated_at timestamptz not null default now()
);

create index if not exists idx_caas_cards_user_status
  on public.caas_cards (user_id, status);

drop trigger if exists trg_caas_cards_updated_at on public.caas_cards;
create trigger trg_caas_cards_updated_at
before update on public.caas_cards
for each row
execute function public.set_updated_at();

create table if not exists public.caas_transactions (
  tx_id bigint generated always as identity primary key,
  user_id uuid not null references public.caas_users(user_id) on delete cascade,
  tx_type text not null check (tx_type in ('internal_transfer', 'external_transfer', 'account_open', 'account_close', 'card_open', 'card_close')),
  from_account_id uuid references public.caas_accounts(account_id),
  to_account_id uuid references public.caas_accounts(account_id),
  amount numeric(14,2),
  currency text,
  status text not null check (status in ('approved', 'rejected', 'pending')),
  reason text,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index if not exists idx_caas_transactions_user_created_at
  on public.caas_transactions (user_id, created_at desc);
