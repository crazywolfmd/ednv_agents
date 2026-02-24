from __future__ import annotations

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from src.settings import settings


SYSTEM_PROMPT = (
    "You are a concise assistant for a starter LangGraph project. "
    "Answer clearly and keep responses practical."
)


def build_chain():
    llm = ChatOpenAI(model=settings.openai_model, temperature=0)
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),
            ("human", "{user_input}"),
        ]
    )
    return prompt | llm
