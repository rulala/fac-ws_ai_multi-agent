from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, START, END
from langgraph.types import Send
from typing import TypedDict, List, Annotated
import operator
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from utils import OrchestratorCodebase

load_dotenv()


class SubTask(BaseModel):
    name: str = Field(description="Name of the subtask")
    description: str = Field(
        description="Detailed description of what needs to be done")
    type: str = Field(
        description="Type of work: 'implementation', 'testing', 'documentation'")


class TaskBreakdown(BaseModel):
    subtasks: List[SubTask] = Field(description="List of subtasks to complete")


class OrchestratorState(TypedDict):
    input: str
    subtasks: List[dict]
    worker_outputs: Annotated[List[str], operator.add]
    final_result: str


class WorkerState(TypedDict):
    subtask: dict


llm = ChatOpenAI(model="gpt-4.1-nano")

orchestrator_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a Task Orchestrator. Break down coding requests into 2-4 specific subtasks. Each subtask should be independently completable."),
    ("human", "Break down this task: {input}")
])

worker_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a specialist worker. Complete ONLY the specific subtask assigned to you. Write clean Python code and ONLY OUTPUT Python code or SQL."),
    ("human", "Subtask: {name}\nDescription: {description}\nType: {type}")
])

synthesis_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a Code Synthesiser. Combine all worker outputs into a cohesive final solution."),
    ("human", "Worker outputs to combine:\n{outputs}")
])


def orchestrator_agent(state: OrchestratorState) -> OrchestratorState:
    structured_llm = llm.with_structured_output(TaskBreakdown)
    response = structured_llm.invoke(
        orchestrator_prompt.format_messages(input=state["input"])
    )

    subtasks = [subtask.model_dump() for subtask in response.subtasks]
    print(f"🎯 Orchestrator created {len(subtasks)} subtasks:")
    for i, task in enumerate(subtasks, 1):
        print(f"  {i}. {task['name']} ({task['type']})")

    return {"subtasks": subtasks, "worker_outputs": []}


def create_workers(state: OrchestratorState):
    return [Send("worker", {"subtask": subtask}) for subtask in state["subtasks"]]


def worker_agent(state: WorkerState) -> dict:
    subtask = state["subtask"]
    response = llm.invoke(worker_prompt.format_messages(
        name=subtask["name"],
        description=subtask["description"],
        type=subtask["type"]
    ))

    print(f"⚡ Worker completed: {subtask['name']}")
    return {"worker_outputs": [response.content]}


def synthesis_agent(state: OrchestratorState) -> OrchestratorState:
    outputs_text = "\n\n---\n\n".join([
        f"Worker {i+1} Output:\n{output}"
        for i, output in enumerate(state["worker_outputs"])
    ])

    response = llm.invoke(
        synthesis_prompt.format_messages(outputs=outputs_text))

    print(
        f"🔄 Synthesiser combined {len(state['worker_outputs'])} worker outputs")
    return {"final_result": response.content}


builder = StateGraph(OrchestratorState)
builder.add_node("orchestrator", orchestrator_agent)
builder.add_node("worker", worker_agent)
builder.add_node("synthesis", synthesis_agent)

builder.add_edge(START, "orchestrator")
builder.add_conditional_edges("orchestrator", create_workers, ["worker"])
builder.add_edge("worker", "synthesis")
builder.add_edge("synthesis", END)

workflow = builder.compile()

if __name__ == "__main__":
    task = "Create a user authentication system with login, registration, and password reset"

    print("Starting orchestrator-worker...")
    result = workflow.invoke({"input": task})

    codebase = OrchestratorCodebase("06_orchestrator_worker", task)
    codebase.generate(result)

    print("=== ORCHESTRATOR WORKFLOW COMPLETED ===")
