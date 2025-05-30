from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from typing import TypedDict
from dotenv import load_dotenv

load_dotenv()


class State(TypedDict):
    input: str
    code: str
    security: str
    performance: str


llm = ChatOpenAI(model="gpt-4.1-nano")


def coder(state: State) -> State:
    response = llm.invoke(f"Write Python code for: {state['input']}")
    return {"code": response.content}


def security_check(state: State) -> State:
    response = llm.invoke(f"Security issues in:\n{state['code']}")
    return {"security": response.content}


def performance_check(state: State) -> State:
    response = llm.invoke(f"Performance issues in:\n{state['code']}")
    return {"performance": response.content}


builder = StateGraph(State)
builder.add_node("coder", coder)
builder.add_node("security_check", security_check)
builder.add_node("performance_check", performance_check)

builder.add_edge(START, "coder")
builder.add_edge("coder", "security_check")
builder.add_edge("coder", "performance_check")
builder.add_edge("security_check", END)
builder.add_edge("performance_check", END)

workflow = builder.compile()

if __name__ == "__main__":
    result = workflow.invoke({"input": "API endpoint with database"})
    print("CODE:", result["code"])
    print("SECURITY:", result["security"])
    print("PERFORMANCE:", result["performance"])