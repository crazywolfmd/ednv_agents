from __future__ import annotations

import streamlit as st

from src.graph import build_graph


st.set_page_config(page_title="Endv Agents", page_icon=":robot_face:")
st.title("Endv Agents")
st.caption("Minimal Streamlit + LangChain + LangGraph + LangSmith starter")

graph = build_graph()

if "history" not in st.session_state:
    st.session_state.history = []

for turn in st.session_state.history:
    st.markdown(f"**You:** {turn['user']}")
    st.markdown(f"**Assistant:** {turn['assistant']}")

user_input = st.text_input("Ask anything", placeholder="Explain LangGraph in one paragraph")

if st.button("Send", type="primary", use_container_width=True) and user_input.strip():
    result = graph.invoke({"user_input": user_input, "response": ""})
    answer = result["response"]
    st.session_state.history.append({"user": user_input, "assistant": answer})
    st.rerun()
