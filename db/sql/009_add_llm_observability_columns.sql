-- 009_add_llm_observability_columns.sql
-- Adds provider and runtime observability fields for LLM analytics.

alter table public.caas_chat_messages
  add column if not exists llm_provider text,
  add column if not exists llm_latency_ms integer,
  add column if not exists llm_raw_usage jsonb not null default '{}'::jsonb;

-- Optional quality guard for known providers.
alter table public.caas_chat_messages
  drop constraint if exists caas_chat_messages_llm_provider_check;

alter table public.caas_chat_messages
  add constraint caas_chat_messages_llm_provider_check
  check (
    llm_provider is null
    or llm_provider in ('openai', 'huggingface')
  );
