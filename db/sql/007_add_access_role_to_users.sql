-- 007_add_access_role_to_users.sql
-- Adds role column for role-based UI/feature access.

alter table public.caas_users
  add column if not exists access_role text not null default 'user';

-- Ensure allowed values and normalize invalid/empty values.
update public.caas_users
set access_role = 'user'
where access_role is null
   or trim(access_role) = ''
   or access_role not in ('admin', 'user');

alter table public.caas_users
  drop constraint if exists caas_users_access_role_check;

alter table public.caas_users
  add constraint caas_users_access_role_check
  check (access_role in ('admin', 'user'));
