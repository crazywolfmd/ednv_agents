-- 010_backfill_llm_provider.sql
-- Optional backfill for historical rows where provider is unknown.
-- Assumes historical data came from OpenAI before provider-switch support.

update public.caas_chat_messages
set llm_provider = 'openai'
where llm_provider is null
  and (
    llm_model is not null
    or llm_total_tokens is not null
    or llm_prompt_tokens is not null
    or llm_completion_tokens is not null
    or llm_calls is not null
  );


