from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Literal
from dotenv import load_dotenv

load_dotenv()


class State(TypedDict):
    input: str
    code: str
    score: int
    iterations: int


llm = ChatOpenAI(model="gpt-4.1-nano")


def generator(state: State) -> State:
    response = llm.invoke(f"Write Python code for: {state['input']}")
    return {"code": response.content, "iterations": state.get("iterations", 0)}


def evaluator(state: State) -> State:
    response = llm.invoke(f"Rate code quality 1-10:\n{state['code']}\nJust the number:")
    try:
        score = int(response.content.strip())
    except:
        score = 5
    return {"score": score}


def optimiser(state: State) -> State:
    response = llm.invoke(f"Improve this code:\n{state['code']}")
    return {"code": response.content, "iterations": state["iterations"] + 1}


def should_continue(state: State) -> Literal["optimise", "done"]:
    if state.get("iterations", 0) >= 2:
        return "done"
    if state.get("score", 0) >= 8:
        return "done"
    return "optimise"


builder = StateGraph(State)
builder.add_node("generator", generator)
builder.add_node("evaluator", evaluator)
builder.add_node("optimiser", optimiser)

builder.add_edge(START, "generator")
builder.add_edge("generator", "evaluator")
builder.add_conditional_edges("evaluator", should_continue, {"optimise": "optimiser", "done": END})
builder.add_edge("optimiser", "evaluator")

workflow = builder.compile()

if __name__ == "__main__":
    result = workflow.invoke({"input": "file upload API"})
    print(f"FINAL CODE (Score: {result['score']}, Iterations: {result['iterations']}):")
    print(result["code"])