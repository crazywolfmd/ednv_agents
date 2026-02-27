-- 012_backfill_llm_provider_by_model.sql
-- Backfill llm_provider for historical assistant rows where provider is null/empty.

update public.caas_chat_messages
set llm_provider = case
  when coalesce(lower(llm_model), '') like 'gpt%' then 'openai'
  when coalesce(lower(llm_model), '') like 'o1%' then 'openai'
  when coalesce(lower(llm_model), '') like 'o3%' then 'openai'
  when coalesce(lower(llm_model), '') like '%llama%' then 'huggingface'
  when coalesce(lower(llm_model), '') like 'meta-llama/%' then 'huggingface'
  when coalesce(lower(llm_model), '') like 'mistralai/%' then 'huggingface'
  when coalesce(lower(llm_model), '') like 'qwen/%' then 'huggingface'
  else llm_provider
end
where role = 'assistant'
  and coalesce(nullif(llm_provider, ''), '') = ''
  and coalesce(nullif(llm_model, ''), '') <> '';

-- Optional final fallback for remaining rows with usage but unknown model.
update public.caas_chat_messages
set llm_provider = 'openai'
where role = 'assistant'
  and coalesce(nullif(llm_provider, ''), '') = ''
  and coalesce(nullif(llm_model, ''), '') = ''
  and (
    llm_total_tokens is not null
    or llm_prompt_tokens is not null
    or llm_completion_tokens is not null
    or llm_calls is not null
  );
