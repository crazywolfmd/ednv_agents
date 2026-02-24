from __future__ import annotations

from typing import TypedDict

from langgraph.graph import END, START, StateGraph
from langsmith import traceable

from src.chains import build_chain


class AgentState(TypedDict):
    user_input: str
    response: str


@traceable(name="call_model")
def call_model(state: AgentState) -> AgentState:
    chain = build_chain()
    output = chain.invoke({"user_input": state["user_input"]})
    return {"user_input": state["user_input"], "response": output.content}


def build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("model", call_model)
    graph.add_edge(START, "model")
    graph.add_edge("model", END)
    return graph.compile()
