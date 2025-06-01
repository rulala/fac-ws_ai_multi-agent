from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Literal
from dotenv import load_dotenv

load_dotenv()


class State(TypedDict):
    input: str
    code: str
    score: int


llm = ChatOpenAI(model="gpt-4.1-nano")


def coder(state: State) -> State:
    response = llm.invoke(f"Write Python code for: {state['input']}")
    return {"code": response.content}


def evaluator(state: State) -> State:
    response = llm.invoke(f"Rate this code 1-10:\n{state['code']}\nRespond with just the number.")
    try:
        score = int(response.content.strip())
    except:
        score = 5
    return {"score": score}


def improver(state: State) -> State:
    response = llm.invoke(f"Improve this code:\n{state['code']}")
    return {"code": response.content}


def quality_gate(state: State) -> Literal["improve", "done"]:
    return "done" if state["score"] >= 7 else "improve"


builder = StateGraph(State)
builder.add_node("coder", coder)
builder.add_node("evaluator", evaluator)
builder.add_node("improver", improver)

builder.add_edge(START, "coder")
builder.add_edge("coder", "evaluator")
builder.add_conditional_edges("evaluator", quality_gate, {"improve": "improver", "done": END})
builder.add_edge("improver", "evaluator")

workflow = builder.compile()

if __name__ == "__main__":
    result = workflow.invoke({"input": "file upload function"})
    print(f"FINAL CODE (Score: {result['score']}):")
    print(result["code"])