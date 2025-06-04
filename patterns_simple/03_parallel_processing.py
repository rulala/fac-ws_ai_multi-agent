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
    report: str


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


def synthesis_agent(state: State) -> State:
    analyses = [state["security"], state["performance"]]
    combined = "\n\n".join(analyses)
    response = llm.invoke(f"Synthesise these analyses:\n{combined}")
    return {"report": response.content}


builder = StateGraph(State)
builder.add_node("coder", coder)
builder.add_node("security_check", security_check)
builder.add_node("performance_check", performance_check)
builder.add_node("synthesis_agent", synthesis_agent)

builder.add_edge(START, "coder")
builder.add_edge("coder", "security_check")
builder.add_edge("coder", "performance_check")
builder.add_edge("security_check", "synthesis_agent")
builder.add_edge("performance_check", "synthesis_agent")
builder.add_edge("synthesis_agent", END)

workflow = builder.compile()

if __name__ == "__main__":
    result = workflow.invoke({"input": "API endpoint with database"})
    print("CODE:", result["code"])
    print("SYNTHESIS:", result["report"])
