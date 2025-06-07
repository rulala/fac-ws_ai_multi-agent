from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.types import Send
from typing import TypedDict, List, Annotated
import operator
from dotenv import load_dotenv

load_dotenv()


class State(TypedDict):
    input: str
    subtasks: List[str]
    worker_outputs: Annotated[List[str], operator.add]
    final_result: str


class WorkerState(TypedDict):
    task: str


llm = ChatOpenAI(model="gpt-4.1-nano")


def orchestrator(state: State) -> State:
    response = llm.invoke(
        f"Break down this coding task into 3 simple subtasks: {state['input']}")

    lines = response.content.strip().split('\n')
    subtasks = [line.strip('- ').strip() for line in lines if line.strip()][:3]

    print(f"Orchestrator created {len(subtasks)} subtasks")
    return {"subtasks": subtasks, "worker_outputs": []}


def create_workers(state: State):
    return [Send("worker", {"task": task}) for task in state["subtasks"]]


def worker(state: WorkerState) -> WorkerState:
    response = llm.invoke(f"Complete this coding subtask: {state['task']}")
    print(f"Worker completed: {state['task'][:30]}...")
    return {"worker_outputs": [response.content]}


def collect_results(state: State) -> State:
    return state


def synthesiser(state: State) -> State:
    combined = "\n\n".join(state["worker_outputs"])
    response = llm.invoke(
        f"Combine these code pieces into one solution:\n{combined}")
    return {"final_result": response.content}


builder = StateGraph(State)
builder.add_node("orchestrator", orchestrator)
builder.add_node("worker", worker)
builder.add_node("collect_results", collect_results)
builder.add_node("synthesiser", synthesiser)

builder.add_edge(START, "orchestrator")
builder.add_conditional_edges("orchestrator", create_workers, ["worker"])
builder.add_edge("worker", "collect_results")
builder.add_edge("collect_results", "synthesiser")
builder.add_edge("synthesiser", END)

workflow = builder.compile()

if __name__ == "__main__":
    result = workflow.invoke({"input": "email validation API endpoint"})
    print("FINAL RESULT:")
    print(result["final_result"])
