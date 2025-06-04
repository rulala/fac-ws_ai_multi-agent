from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Literal
from dotenv import load_dotenv

load_dotenv()


class State(TypedDict):
    input: str
    code: str
    expert_reports: list
    next_expert: str


llm = ChatOpenAI(model="gpt-4.1-nano")


def coder(state: State) -> State:
    response = llm.invoke(f"Write Python code for: {state['input']}")
    return {"code": response.content, "expert_reports": []}


def supervisor(state: State) -> State:
    completed = len(state.get("expert_reports", []))
    experts = ["security", "quality"]

    if completed < len(experts):
        return {"next_expert": experts[completed]}
    return {"next_expert": "done"}


def security_expert(state: State) -> State:
    response = llm.invoke(f"Security analysis:\n{state['code']}")
    reports = state.get("expert_reports", [])
    reports.append(f"Security: {response.content}")
    return {"expert_reports": reports}


def quality_expert(state: State) -> State:
    response = llm.invoke(f"Quality analysis:\n{state['code']}")
    reports = state.get("expert_reports", [])
    reports.append(f"Quality: {response.content}")
    return {"expert_reports": reports}


def route_expert(state: State) -> Literal["security_expert", "quality_expert", "done"]:
    next_expert = state.get("next_expert", "done")
    if next_expert == "security":
        return "security_expert"
    elif next_expert == "quality":
        return "quality_expert"
    return "done"


builder = StateGraph(State)
builder.add_node("coder", coder)
builder.add_node("supervisor", supervisor)
builder.add_node("security_expert", security_expert)
builder.add_node("quality_expert", quality_expert)

builder.add_edge(START, "coder")
builder.add_edge("coder", "supervisor")
builder.add_conditional_edges("supervisor", route_expert, {
    "security_expert": "security_expert",
    "quality_expert": "quality_expert",
    "done": END
})
builder.add_edge("security_expert", "supervisor")
builder.add_edge("quality_expert", "supervisor")

workflow = builder.compile()

if __name__ == "__main__":
    result = workflow.invoke({"input": "user authentication system"})
    print("CODE:", result["code"])
    print("EXPERT REPORTS:")
    for report in result["expert_reports"]:
        print(f"- {report}")
