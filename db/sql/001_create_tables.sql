-- 001_create_tables.sql
-- Run first in Supabase SQL Editor.

create extension if not exists pgcrypto;

create or replace function public.set_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

create table if not exists public.caas_users (
  user_id uuid primary key default gen_random_uuid(),
  username text not null unique,
  name text,
  lastname text,
  email text not null unique,
  password_hash text not null,
  access_role text not null default 'user' check (access_role in ('admin', 'user')),
  is_active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

drop trigger if exists trg_caas_users_updated_at on public.caas_users;
create trigger trg_caas_users_updated_at
before update on public.caas_users
for each row
execute function public.set_updated_at();

create table if not exists public.caas_chat_messages (
  id bigint generated always as identity primary key,
  user_id uuid not null references public.caas_users(user_id) on delete cascade,
  role text not null check (role in ('system', 'user', 'assistant')),
  content text not null,
  created_at timestamptz not null default now()
);

create index if not exists idx_caas_chat_messages_user_created_at
  on public.caas_chat_messages (user_id, created_at desc);

create table if not exists public.caas_user_access_logs (
  id bigint generated always as identity primary key,
  user_id uuid references public.caas_users(user_id) on delete set null,
  identifier text,
  event_type text not null check (event_type in ('login_success', 'login_failed', 'logout')),
  ip_address text,
  user_agent text,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index if not exists idx_caas_user_access_logs_user_created_at
  on public.caas_user_access_logs (user_id, created_at desc);
