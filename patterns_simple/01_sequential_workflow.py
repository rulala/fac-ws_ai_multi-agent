from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from typing import TypedDict
from dotenv import load_dotenv

load_dotenv()


class State(TypedDict):
    input: str
    code: str
    review: str


llm = ChatOpenAI(model="gpt-4.1-nano")


def coder(state: State) -> State:
    response = llm.invoke(f"Write Python code for: {state['input']}")
    return {"code": response.content}


def reviewer(state: State) -> State:
    response = llm.invoke(f"Review this code:\n{state['code']}")
    return {"review": response.content}


builder = StateGraph(State)
builder.add_node("coder", coder)
builder.add_node("reviewer", reviewer)

builder.add_edge(START, "coder")
builder.add_edge("coder", "reviewer")
builder.add_edge("reviewer", END)

workflow = builder.compile()

if __name__ == "__main__":
    result = workflow.invoke({"input": "email validator function"})
    print("CODE:", result["code"])
    print("REVIEW:", result["review"])
