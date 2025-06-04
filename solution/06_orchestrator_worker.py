from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, START, END
from langgraph.types import Send
from typing import TypedDict, List, Annotated, Literal
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
        description="Type of work: 'frontend', 'backend', 'database', 'testing'")
    dependencies: List[str] = Field(
        description="List of subtask names this depends on", default_factory=list)
    priority: int = Field(
        description="Priority level (1=highest, 3=lowest)", default=2)


class TaskBreakdown(BaseModel):
    subtasks: List[SubTask] = Field(description="List of subtasks to complete")


class ValidationResult(BaseModel):
    can_combine: bool = Field(
        description="Whether outputs can be successfully combined")
    issues: List[str] = Field(description="List of integration issues found")
    suggestions: List[str] = Field(description="Suggestions for improvement")


class OrchestratorState(TypedDict):
    input: str
    subtasks: List[dict]
    completed_subtasks: List[str]
    worker_outputs: Annotated[List[str], operator.add]
    validation_result: dict
    final_result: str


class WorkerState(TypedDict):
    subtask: dict


llm = ChatOpenAI(model="gpt-4.1-nano")

orchestrator_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a Task Orchestrator. Analyse the task and break it into 2-4 specific subtasks with clear types (frontend, backend, database, testing) and dependencies. Consider what must be done first."),
    ("human", "Break down this task: {input}")
])

frontend_worker_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a Frontend Specialist. Create user interfaces, HTML, CSS, JavaScript, React components. Write clean, responsive frontend code."),
    ("human", "Frontend task: {name}\nDescription: {description}")
])

backend_worker_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a Backend Specialist. Create APIs, business logic, server-side code. Write clean Python/Node.js backend code with proper error handling."),
    ("human", "Backend task: {name}\nDescription: {description}")
])

database_worker_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a Database Specialist. Design schemas, write SQL queries, handle data persistence. Create efficient, normalised database solutions."),
    ("human", "Database task: {name}\nDescription: {description}")
])

testing_worker_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a Testing Specialist. Write comprehensive tests including unit tests, integration tests, and test scenarios."),
    ("human", "Testing task: {name}\nDescription: {description}")
])

validation_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a Technical Validator. Analyse if these code outputs can be integrated successfully. Check for compatibility, missing connections, and integration issues."),
    ("human", "Validate integration of these outputs:\n{outputs}")
])

synthesis_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a Code Synthesiser. Combine validated worker outputs into a cohesive final solution. Address any integration issues noted by the validator."),
    ("human",
     "Worker outputs:\n{outputs}\n\nValidation results:\n{validation}")
])


def orchestrator_agent(state: OrchestratorState) -> OrchestratorState:
    structured_llm = llm.with_structured_output(TaskBreakdown)
    response = structured_llm.invoke(
        orchestrator_prompt.format_messages(input=state["input"]))

    subtasks = [subtask.model_dump() for subtask in response.subtasks]

    subtasks_by_priority = {}
    for task in subtasks:
        priority = task.get("priority", 2)
        if priority not in subtasks_by_priority:
            subtasks_by_priority[priority] = []
        subtasks_by_priority[priority].append(task)

    ordered_subtasks = []
    for priority in sorted(subtasks_by_priority.keys()):
        ordered_subtasks.extend(subtasks_by_priority[priority])

    print(f"🎯 Orchestrator created {len(subtasks)} subtasks:")
    for i, task in enumerate(ordered_subtasks, 1):
        deps = ", ".join(task["dependencies"]
                         ) if task["dependencies"] else "None"
        print(f"  {i}. {task['name']} ({task['type']}) - Dependencies: {deps}")

    return {"subtasks": ordered_subtasks, "worker_outputs": [], "completed_subtasks": []}


def create_workers(state: OrchestratorState):
    available_subtasks = []
    completed = set(state.get("completed_subtasks", []))

    for subtask in state["subtasks"]:
        if subtask["name"] not in completed:
            dependencies_met = all(
                dep in completed for dep in subtask["dependencies"])
            if dependencies_met:
                available_subtasks.append(subtask)

    return [Send("worker", {"subtask": subtask}) for subtask in available_subtasks]


def check_workers_needed(state: OrchestratorState) -> Literal["workers", "validation"]:
    completed = set(state.get("completed_subtasks", []))

    for subtask in state["subtasks"]:
        if subtask["name"] not in completed:
            dependencies_met = all(
                dep in completed for dep in subtask["dependencies"])
            if dependencies_met:
                return "workers"

    return "validation"


def frontend_worker_agent(state: WorkerState) -> dict:
    subtask = state["subtask"]
    response = llm.invoke(frontend_worker_prompt.format_messages(
        name=subtask["name"],
        description=subtask["description"]
    ))
    print(f"🎨 Frontend worker completed: {subtask['name']}")
    return {"worker_outputs": [f"FRONTEND - {subtask['name']}:\n{response.content}"]}


def backend_worker_agent(state: WorkerState) -> dict:
    subtask = state["subtask"]
    response = llm.invoke(backend_worker_prompt.format_messages(
        name=subtask["name"],
        description=subtask["description"]
    ))
    print(f"⚙️ Backend worker completed: {subtask['name']}")
    return {"worker_outputs": [f"BACKEND - {subtask['name']}:\n{response.content}"]}


def database_worker_agent(state: WorkerState) -> dict:
    subtask = state["subtask"]
    response = llm.invoke(database_worker_prompt.format_messages(
        name=subtask["name"],
        description=subtask["description"]
    ))
    print(f"🗄️ Database worker completed: {subtask['name']}")
    return {"worker_outputs": [f"DATABASE - {subtask['name']}:\n{response.content}"]}


def testing_worker_agent(state: WorkerState) -> dict:
    subtask = state["subtask"]
    response = llm.invoke(testing_worker_prompt.format_messages(
        name=subtask["name"],
        description=subtask["description"]
    ))
    print(f"🧪 Testing worker completed: {subtask['name']}")
    return {"worker_outputs": [f"TESTING - {subtask['name']}:\n{response.content}"]}


def worker_agent(state: WorkerState) -> dict:
    subtask = state["subtask"]
    worker_type = subtask["type"]

    if worker_type == "frontend":
        return frontend_worker_agent(state)
    elif worker_type == "backend":
        return backend_worker_agent(state)
    elif worker_type == "database":
        return database_worker_agent(state)
    elif worker_type == "testing":
        return testing_worker_agent(state)
    else:
        response = llm.invoke(
            f"Complete this task: {subtask['name']} - {subtask['description']}")
        print(f"⚡ Generic worker completed: {subtask['name']}")
        return {"worker_outputs": [f"GENERIC - {subtask['name']}:\n{response.content}"]}


def track_completion(state: OrchestratorState) -> OrchestratorState:
    completed = state.get("completed_subtasks", [])
    worker_outputs = state.get("worker_outputs", [])

    for subtask in state["subtasks"]:
        subtask_name = subtask["name"]
        if subtask_name not in completed:
            for output in worker_outputs:
                if subtask_name in output:
                    completed.append(subtask_name)
                    print(f"✅ Marked '{subtask_name}' as completed")
                    break

    print(
        f"📋 Completion status: {len(completed)}/{len(state['subtasks'])} tasks done")
    return {"completed_subtasks": completed}


def validation_agent(state: OrchestratorState) -> OrchestratorState:
    worker_outputs = state.get("worker_outputs", [])
    outputs_text = "\n\n---\n\n".join(worker_outputs)

    structured_llm = llm.with_structured_output(ValidationResult)
    validation = structured_llm.invoke(
        validation_prompt.format_messages(outputs=outputs_text))

    validation_dict = {
        "can_combine": validation.can_combine,
        "issues": validation.issues,
        "suggestions": validation.suggestions
    }

    if validation.can_combine:
        print("✅ Validation passed - outputs can be integrated")
    else:
        print(f"⚠️ Validation issues found: {len(validation.issues)} issues")
        for issue in validation.issues[:3]:
            print(f"  - {issue}")

    return {"validation_result": validation_dict}


def synthesis_agent(state: OrchestratorState) -> OrchestratorState:
    worker_outputs = state.get("worker_outputs", [])
    outputs_text = "\n\n---\n\n".join(worker_outputs)
    validation_text = str(state.get("validation_result", {}))

    response = llm.invoke(synthesis_prompt.format_messages(
        outputs=outputs_text,
        validation=validation_text
    ))

    print(f"🔄 Synthesiser integrated {len(worker_outputs)} worker outputs")
    return {"final_result": response.content}


def check_completion(state: OrchestratorState) -> bool:
    completed = len(state.get("completed_subtasks", []))
    total = len(state.get("subtasks", []))
    return completed >= total


builder = StateGraph(OrchestratorState)
builder.add_node("orchestrator", orchestrator_agent)
builder.add_node("worker", worker_agent)
builder.add_node("track_completion", track_completion)
builder.add_node("validation", validation_agent)
builder.add_node("synthesis", synthesis_agent)

builder.add_edge(START, "orchestrator")
builder.add_conditional_edges("orchestrator", create_workers, ["worker"])
builder.add_edge("worker", "track_completion")
builder.add_conditional_edges("track_completion", check_workers_needed, {
                              "workers": "create_workers_node", "validation": "validation"})
builder.add_node("create_workers_node", lambda state: state)
builder.add_conditional_edges(
    "create_workers_node", create_workers, ["worker"])
builder.add_edge("validation", "synthesis")
builder.add_edge("synthesis", END)

workflow = builder.compile()

if __name__ == "__main__":
    task = "Create a user authentication system with database, API endpoints, frontend login form, and comprehensive tests"

    print("Starting orchestrator-worker with dependencies...")
    result = workflow.invoke({"input": task})

    codebase = OrchestratorCodebase("06_orchestrator_worker", task)
    codebase.generate(result)

    print("=== WORKFLOW COMPLETED ===")
