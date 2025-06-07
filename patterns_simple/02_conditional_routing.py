from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Literal
from dotenv import load_dotenv

load_dotenv()


class State(TypedDict):
    input: str
    code: str
    route: str
    analysis: str


llm = ChatOpenAI(model="gpt-4.1-nano")


def coder(state: State) -> State:
    response = llm.invoke(f"Write Python code for: {state['input']}")
    return {"code": response.content}


def router(state: State) -> State:
    response = llm.invoke(
        f"Analyze this code. Respond with 'security', 'performance', or 'general':\n{state['code']}")
    route = response.content.strip().lower()
    if route not in ["security", "performance", "general"]:
        route = "general"
    return {"route": route}


def security_expert(state: State) -> State:
    response = llm.invoke(f"Security analysis:\n{state['code']}")
    return {"analysis": response.content}


def performance_expert(state: State) -> State:
    response = llm.invoke(f"Performance analysis:\n{state['code']}")
    return {"analysis": response.content}


def general_expert(state: State) -> State:
    response = llm.invoke(f"General analysis:\n{state['code']}")
    return {"analysis": response.content}


def route_to_expert(state: State) -> Literal["security_expert", "performance_expert", "general_expert"]:
    route = state.get("route", "general")
    return f"{route}_expert"


builder = StateGraph(State)
builder.add_node("coder", coder)
builder.add_node("router", router)
builder.add_node("security_expert", security_expert)
builder.add_node("performance_expert", performance_expert)
builder.add_node("general_expert", general_expert)

builder.add_edge(START, "coder")
builder.add_edge("coder", "router")
builder.add_conditional_edges("router", route_to_expert, {
    "security_expert": "security_expert",
    "performance_expert": "performance_expert",
    "general_expert": "general_expert"
})
builder.add_edge("security_expert", END)
builder.add_edge("performance_expert", END)
builder.add_edge("general_expert", END)

workflow = builder.compile()

if __name__ == "__main__":
    result = workflow.invoke({"input": "user authentication system"})
    print("CODE:", result["code"])
    print("ROUTED TO:", result["route"])
    print("ANALYSIS:", result["analysis"])
