from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Literal
from dotenv import load_dotenv
from utils import EvaluatorCodebase

load_dotenv()


class OptimisationState(TypedDict):
    input: str
    code: list
    security_score: int
    performance_score: int
    readability_score: int
    lowest_score: int
    iteration_count: int
    best_code_index: int
    best_lowest_score: int
    final_code: str


llm = ChatOpenAI(model="gpt-4.1-nano")

# Configuration constants
QUALITY_THRESHOLD = 7
MAX_ITERATIONS = 3
FAST_TRACK_THRESHOLD = 8

generator_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a Senior Software Engineer. Write ONLY Python code - no bash commands, no installation instructions, just the Python implementation."),
    ("human", "{input}")
])

security_evaluator_prompt = ChatPromptTemplate.from_messages([
    ("system", "Rate this code's SECURITY from 1-10. Consider input validation, injection risks, authentication. Respond with just the number."),
    ("human", "Code:\n{code}")
])

performance_evaluator_prompt = ChatPromptTemplate.from_messages([
    ("system", "Rate this code's PERFORMANCE from 1-10. Consider algorithmic complexity, efficiency, resource usage. Respond with just the number."),
    ("human", "Code:\n{code}")
])

readability_evaluator_prompt = ChatPromptTemplate.from_messages([
    ("system", "Rate this code's READABILITY from 1-10. Consider naming, structure, documentation, clarity. Respond with just the number."),
    ("human", "Code:\n{code}")
])

optimiser_prompt = ChatPromptTemplate.from_messages([
    ("system", "Improve code based on the weakest scoring area. Focus on the lowest score area."),
    ("human", "Code:\n{code}\n\nScores - Security: {security}, Performance: {performance}, Readability: {readability}\n\nImprove the weakest area:")
])


def code_generator(state: OptimisationState) -> OptimisationState:
    response = llm.invoke(
        generator_prompt.format_messages(input=state["input"]))
    return {
        "code": [response.content],
        "iteration_count": 0,
        "best_code_index": 0,
        "best_lowest_score": 0
    }


def multi_criteria_evaluator_agent(state: OptimisationState) -> OptimisationState:
    current_code = state["code"][-1] if state["code"] else ""
    current_iteration = len(state["code"]) - 1

    security_response = llm.invoke(
        security_evaluator_prompt.format_messages(code=current_code))
    performance_response = llm.invoke(
        performance_evaluator_prompt.format_messages(code=current_code))
    readability_response = llm.invoke(
        readability_evaluator_prompt.format_messages(code=current_code))

    try:
        security_score = int(security_response.content.strip())
    except:
        security_score = 5

    try:
        performance_score = int(performance_response.content.strip())
    except:
        performance_score = 5

    try:
        readability_score = int(readability_response.content.strip())
    except:
        readability_score = 5

    lowest_score = min(security_score, performance_score, readability_score)

    print(
        f"📊 Scores - Security: {security_score}, Performance: {performance_score}, Readability: {readability_score} (Lowest: {lowest_score})")

    # Track best version
    best_code_index = state.get("best_code_index", 0)
    best_lowest_score = state.get("best_lowest_score", 0)

    if lowest_score > best_lowest_score:
        best_code_index = current_iteration
        best_lowest_score = lowest_score
        print(f"🏆 New best code found! Score: {lowest_score}/10")

    return {
        "security_score": security_score,
        "performance_score": performance_score,
        "readability_score": readability_score,
        "lowest_score": lowest_score,
        "best_code_index": best_code_index,
        "best_lowest_score": best_lowest_score
    }


def optimiser_agent(state: OptimisationState) -> OptimisationState:
    current_code = state["code"][-1] if state["code"] else ""

    response = llm.invoke(optimiser_prompt.format_messages(
        code=current_code,
        security=state["security_score"],
        performance=state["performance_score"],
        readability=state["readability_score"]
    ))

    updated_code_list = state["code"] + [response.content]
    return {
        "code": updated_code_list,
        "iteration_count": state["iteration_count"] + 1
    }


def finalise_best_code(state: OptimisationState) -> OptimisationState:
    best_index = state.get("best_code_index", len(state["code"]) - 1)
    best_code = state["code"][best_index]

    if best_index != len(state["code"]) - 1:
        print(
            f"🎯 Selected best code from iteration {best_index + 1} (score: {state['best_lowest_score']}/10) instead of final iteration")

    return {"final_code": best_code}


def should_continue_optimisation(state: OptimisationState) -> Literal["optimise", "finalise"]:
    iteration_count = state.get("iteration_count", 0)
    lowest_score = state.get("lowest_score", 0)

    # Fast track: Skip optimization if initial score is high enough
    if iteration_count == 0 and lowest_score >= FAST_TRACK_THRESHOLD:
        print(
            f"🚀 Fast track activated! All scores ≥ {FAST_TRACK_THRESHOLD} - skipping optimization")
        return "finalise"

    # Max iterations reached
    if iteration_count >= MAX_ITERATIONS:
        print(
            f"Max iterations reached. Best score achieved: {state.get('best_lowest_score', 0)}/10")
        return "finalise"

    # Quality threshold reached
    if lowest_score >= QUALITY_THRESHOLD and iteration_count > 0:
        print(f"✅ Quality threshold reached! Lowest score: {lowest_score}/10")
        return "finalise"

    return "optimise"


builder = StateGraph(OptimisationState)
builder.add_node("generator", code_generator)
builder.add_node("evaluator", multi_criteria_evaluator_agent)
builder.add_node("optimiser", optimiser_agent)
builder.add_node("finalise", finalise_best_code)

builder.add_edge(START, "generator")
builder.add_edge("generator", "evaluator")
builder.add_conditional_edges(
    "evaluator",
    should_continue_optimisation,
    {"optimise": "optimiser", "finalise": "finalise"}
)
builder.add_edge("optimiser", "evaluator")
builder.add_edge("finalise", END)

workflow = builder.compile()

if __name__ == "__main__":
    task = "Write a REST API endpoint for file upload with validation"

    print("Starting iterative optimisation...")
    result = workflow.invoke({"input": task})

    codebase = EvaluatorCodebase("05_evaluator_optimiser", task)
    codebase.generate(result)

    print("=== WORKFLOW COMPLETED ===")
