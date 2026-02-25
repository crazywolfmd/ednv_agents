-- 005_add_llm_token_usage_columns.sql
-- Run after 001 to store LLM token usage per chat assistant message.

alter table public.caas_chat_messages
  add column if not exists llm_model text,
  add column if not exists llm_prompt_tokens integer,
  add column if not exists llm_completion_tokens integer,
  add column if not exists llm_total_tokens integer,
  add column if not exists llm_calls integer;
