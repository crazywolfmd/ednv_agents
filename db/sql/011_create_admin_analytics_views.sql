-- 011_create_admin_analytics_views.sql
-- Creates reusable analytics views for the admin console.

create or replace view public.caas_admin_vw_kpis as
select
  (select count(*)::bigint from public.caas_users) as total_users,
  (select count(*)::bigint from public.caas_users where is_active = true) as active_users,
  (select count(*)::bigint from public.caas_users where access_role = 'admin') as admin_users,
  (select count(*)::bigint from public.caas_accounts) as total_accounts,
  (select count(*)::bigint from public.caas_accounts where status = 'active') as active_accounts,
  (select count(*)::bigint from public.caas_cards) as total_cards,
  (select count(*)::bigint from public.caas_cards where status = 'active') as active_cards,
  (select count(*)::bigint from public.caas_chat_messages) as total_chat_messages,
  (select count(*)::bigint from public.caas_chat_messages where role = 'user') as user_messages,
  (select count(*)::bigint from public.caas_chat_messages where role = 'assistant') as assistant_messages,
  (select coalesce(sum(llm_prompt_tokens), 0)::bigint from public.caas_chat_messages where role = 'assistant') as total_prompt_tokens,
  (select coalesce(sum(llm_completion_tokens), 0)::bigint from public.caas_chat_messages where role = 'assistant') as total_completion_tokens,
  (select coalesce(sum(llm_total_tokens), 0)::bigint from public.caas_chat_messages where role = 'assistant') as total_tokens,
  (select coalesce(sum(llm_calls), 0)::bigint from public.caas_chat_messages where role = 'assistant') as total_llm_calls,
  (
    select coalesce(avg(llm_total_tokens), 0)::numeric(18,2)
    from public.caas_chat_messages
    where role = 'assistant'
      and llm_total_tokens is not null
  ) as avg_tokens_per_assistant,
  (
    select count(*)::bigint
    from public.caas_user_access_logs
    where event_type = 'login_success'
      and created_at >= now() - interval '24 hours'
  ) as login_success_24h,
  (
    select count(*)::bigint
    from public.caas_user_access_logs
    where event_type = 'login_failed'
      and created_at >= now() - interval '24 hours'
  ) as login_failed_24h,
  (select count(*)::bigint from public.caas_transactions) as total_transactions,
  (select count(*)::bigint from public.caas_transactions where status = 'approved') as approved_transactions,
  (select count(*)::bigint from public.caas_transactions where status = 'rejected') as rejected_transactions,
  (select count(*)::bigint from public.caas_transactions where status = 'pending') as pending_transactions;

create or replace view public.caas_admin_vw_daily_usage as
select
  created_at::date as day,
  count(*)::bigint as total_messages,
  count(*) filter (where role = 'user')::bigint as user_messages,
  count(*) filter (where role = 'assistant')::bigint as assistant_messages,
  coalesce(sum(llm_prompt_tokens), 0)::bigint as prompt_tokens,
  coalesce(sum(llm_completion_tokens), 0)::bigint as completion_tokens,
  coalesce(sum(llm_total_tokens), 0)::bigint as total_tokens,
  coalesce(sum(llm_calls), 0)::bigint as llm_calls
from public.caas_chat_messages
group by created_at::date
order by day desc;

create or replace view public.caas_admin_vw_provider_usage as
select
  coalesce(nullif(llm_provider, ''), 'unknown') as llm_provider,
  count(*)::bigint as assistant_messages,
  coalesce(sum(llm_prompt_tokens), 0)::bigint as prompt_tokens,
  coalesce(sum(llm_completion_tokens), 0)::bigint as completion_tokens,
  coalesce(sum(llm_total_tokens), 0)::bigint as total_tokens,
  coalesce(sum(llm_calls), 0)::bigint as llm_calls
from public.caas_chat_messages
where role = 'assistant'
group by coalesce(nullif(llm_provider, ''), 'unknown')
order by total_tokens desc;

create or replace view public.caas_admin_vw_model_usage as
select
  coalesce(nullif(llm_provider, ''), 'unknown') as llm_provider,
  coalesce(nullif(llm_model, ''), 'unknown') as llm_model,
  count(*)::bigint as assistant_messages,
  coalesce(sum(llm_total_tokens), 0)::bigint as total_tokens,
  coalesce(sum(llm_calls), 0)::bigint as llm_calls,
  coalesce(avg(llm_total_tokens), 0)::numeric(18,2) as avg_tokens_per_message
from public.caas_chat_messages
where role = 'assistant'
group by
  coalesce(nullif(llm_provider, ''), 'unknown'),
  coalesce(nullif(llm_model, ''), 'unknown')
order by total_tokens desc;

create or replace view public.caas_admin_vw_transaction_daily as
select
  created_at::date as day,
  tx_type,
  status,
  count(*)::bigint as tx_count,
  coalesce(sum(amount), 0)::numeric(18,2) as total_amount
from public.caas_transactions
group by created_at::date, tx_type, status
order by day desc, tx_count desc;

create or replace view public.caas_admin_vw_transaction_failures as
select
  created_at,
  user_id,
  tx_id,
  tx_type,
  status,
  currency,
  amount,
  reason
from public.caas_transactions
where status in ('rejected', 'pending')
order by created_at desc;

create or replace view public.caas_admin_vw_auth_daily as
select
  created_at::date as day,
  event_type,
  count(*)::bigint as event_count
from public.caas_user_access_logs
group by created_at::date, event_type
order by day desc;

create or replace view public.caas_admin_vw_entity_status as
select
  'account'::text as entity_type,
  status,
  count(*)::bigint as entity_count
from public.caas_accounts
group by status
union all
select
  'card'::text as entity_type,
  status,
  count(*)::bigint as entity_count
from public.caas_cards
group by status;

create or replace view public.caas_admin_vw_data_quality as
select
  (select count(*)::bigint from public.caas_chat_messages where role = 'assistant' and llm_total_tokens is null) as assistant_missing_total_tokens,
  (select count(*)::bigint from public.caas_chat_messages where role = 'assistant' and coalesce(nullif(llm_provider, ''), '') = '') as assistant_missing_provider,
  (select count(*)::bigint from public.caas_chat_messages where role = 'assistant' and coalesce(nullif(llm_model, ''), '') = '') as assistant_missing_model,
  (
    select count(*)::bigint
    from public.caas_chat_messages
    where role = 'assistant'
      and (
        coalesce(llm_prompt_tokens, 0) < 0
        or coalesce(llm_completion_tokens, 0) < 0
        or coalesce(llm_total_tokens, 0) < 0
      )
  ) as assistant_negative_token_rows,
  (select count(*)::bigint from public.caas_user_access_logs where coalesce(nullif(ip_address, ''), '') = '') as access_logs_missing_ip,
  now() as refreshed_at;
