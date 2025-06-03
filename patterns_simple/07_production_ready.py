from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Literal
from dotenv import load_dotenv

load_dotenv()


class State(TypedDict):
    input: str
    code: str
    approved: bool
    retries: int


llm = ChatOpenAI(model="gpt-4.1-nano")


def coder(state: State) -> State:
    try:
        response = llm.invoke(f"Write production-ready Python code for: {state['input']}")
        return {"code": response.content, "retries": 0}
    except:
        return {"retries": state.get("retries", 0) + 1}


def approver(state: State) -> State:
    response = llm.invoke(f"Is this production-ready? Answer yes/no:\n{state['code']}")
    approved = "yes" in response.content.lower()
    return {"approved": approved}


def error_handler(state: State) -> State:
    print(f"Error occurred, retry {state.get('retries', 0)}")
    return state


def check_status(state: State) -> Literal["retry", "approve"]:
    if state.get("retries", 0) > 0 and state.get("retries", 0) < 3:
        return "retry"
    return "approve"


def check_approval(state: State) -> Literal["deploy", "retry"]:
    if state.get("approved", False):
        return "deploy"
    if state.get("retries", 0) < 3:
        return "retry"
    return "deploy"


def deploy(state: State) -> State:
    print("✅ Deploying to production" if state.get("approved") else "⚠️ Deploying with warnings")
    return state


builder = StateGraph(State)
builder.add_node("coder", coder)
builder.add_node("approver", approver)
builder.add_node("error_handler", error_handler)
builder.add_node("deploy", deploy)

builder.add_edge(START, "coder")
builder.add_conditional_edges("coder", check_status, {"retry": "error_handler", "approve": "approver"})
builder.add_edge("error_handler", "coder")
builder.add_conditional_edges("approver", check_approval, {"deploy": "deploy", "retry": "error_handler"})
builder.add_edge("deploy", END)

workflow = builder.compile()

if __name__ == "__main__":
    result = workflow.invoke({"input": "secure authentication API"})
    print("FINAL CODE:")
    print(result["code"])