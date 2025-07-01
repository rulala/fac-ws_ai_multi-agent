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
    score: int
    scores: int
    iteration_count: int
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
    lowest_scores = state.get("scores", [])
    lowest_scores.append(lowest_score)

    print(
        f"📊 Scores - Security: {security_score}, Performance: {performance_score}, Readability: {readability_score} (Lowest: {lowest_score})")

    return {
        "security_score": security_score,
        "performance_score": performance_score,
        "readability_score": readability_score,
        "score": lowest_score,
        "scores": lowest_scores,
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


def finalise_code(state: OptimisationState) -> OptimisationState:
    final_code = state["code"][-1] if state["code"] else ""
    return {"final_code": final_code}


def should_continue_optimisation(state: OptimisationState) -> Literal["optimise", "finalise"]:
    # Exercise 1: Adjusted thresholds
    quality_threshold = 9  # Changed from 7 to 9
    max_iterations = 5     # Increased from 3 to 5 to accommodate higher threshold

    iteration_count = state.get("iteration_count", 0)
    lowest_score = state.get("score", 0)
    fast_track = state.get("fast_track", False)

    # Exercise 2: Fast track - skip optimization if initial score >= 8
    if fast_track:
        print(f"🚀 Fast track complete! Initial score was ≥ 8, optimization skipped")
        return "finalise"

    if iteration_count >= max_iterations:
        print(
            f"Max iterations ({max_iterations}) reached. Final score: {lowest_score}/10. Quality threshold {quality_threshold}/10 not reached.")
        return "finalise"

    # Exercise 3: Route based on lowest score reaching threshold
    if lowest_score >= quality_threshold and iteration_count > 0:
        print(
            f"✅ Quality threshold ({quality_threshold}) reached! Lowest score: {lowest_score}/10")
        return "finalise"

    return "optimise"


builder = StateGraph(OptimisationState)
builder.add_node("generator", code_generator)
builder.add_node("evaluator", multi_criteria_evaluator_agent)
builder.add_node("optimiser", optimiser_agent)
builder.add_node("finalise", finalise_code)
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
    task = "Write a secure REST API endpoint for file upload with comprehensive validation, error handling, and performance optimization"

    print("Starting iterative optimisation...")
    result = workflow.invoke({"input": task})

    codebase = EvaluatorCodebase("05_evaluator_optimiser", task)
    codebase.generate(result)

    print("=== EVALUATOR-OPTIMISER WORKFLOW COMPLETED ===")
