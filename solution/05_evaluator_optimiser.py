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
    quality_score: int
    quality_scores: list
    security_score: int
    performance_score: int
    readability_score: int
    lowest_score: int
    iteration_count: int
    final_code: str
    fast_track: bool


llm = ChatOpenAI(model="gpt-4.1-nano")

generator_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a Senior Software Engineer. Write ONLY Python code - no bash commands, no installation instructions, just the Python implementation."),
    ("human", "{input}")
])

multi_criteria_evaluator_prompt = ChatPromptTemplate.from_messages([
    ("system", "Rate this code on THREE separate criteria from 1-10. Respond ONLY in this format: 'Security: X, Performance: Y, Readability: Z' where X, Y, Z are numbers 1-10."),
    ("human", "Code:\n{code}")
])

optimiser_prompt = ChatPromptTemplate.from_messages([
    ("system", "Improve this code based on quality concerns. Focus on security, performance, and readability."),
    ("human", "Code:\n{code}")
])


def code_generator(state: OptimisationState) -> OptimisationState:
    response = llm.invoke(
        generator_prompt.format_messages(input=state["input"]))
    return {
        "code": [response.content], 
        "iteration_count": 0, 
        "quality_scores": [],
        "fast_track": False
    }


def multi_criteria_evaluator_agent(state: OptimisationState) -> OptimisationState:
    current_code = state["code"][-1] if state["code"] else ""

    response = llm.invoke(multi_criteria_evaluator_prompt.format_messages(code=current_code))

    # Parse the response to extract individual scores
    try:
        content = response.content.strip()
        # Expected format: "Security: X, Performance: Y, Readability: Z"
        parts = content.split(',')
        security_score = int(parts[0].split(':')[1].strip())
        performance_score = int(parts[1].split(':')[1].strip())
        readability_score = int(parts[2].split(':')[1].strip())
    except:
        # Fallback scores if parsing fails
        security_score = 5
        performance_score = 5
        readability_score = 5

    # Calculate lowest score for routing decisions
    lowest_score = min(security_score, performance_score, readability_score)
    overall_score = lowest_score  # Route based on lowest score

    print(f"📊 Scores - Security: {security_score}, Performance: {performance_score}, Readability: {readability_score} (Lowest: {lowest_score})")

    # Check for fast track on first iteration
    is_first_iteration = state.get("iteration_count", 0) == 0
    fast_track = is_first_iteration and overall_score >= 8
    
    if fast_track:
        print("🚀 Fast track activated! Initial score ≥ 8, skipping optimization")

    # Add score to history
    quality_scores = state.get("quality_scores", [])
    quality_scores.append(overall_score)

    return {
        "quality_score": overall_score,
        "quality_scores": quality_scores,
        "security_score": security_score,
        "performance_score": performance_score,
        "readability_score": readability_score,
        "lowest_score": lowest_score,
        "fast_track": fast_track
    }


def optimiser_agent(state: OptimisationState) -> OptimisationState:
    current_code = state["code"][-1] if state["code"] else ""

    response = llm.invoke(optimiser_prompt.format_messages(code=current_code))

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
    quality_score = state.get("quality_score", 0)
    fast_track = state.get("fast_track", False)

    # Exercise 2: Fast track - skip optimization if initial score >= 8
    if fast_track:
        print(f"🚀 Fast track complete! Initial score was ≥ 8, optimization skipped")
        return "finalise"

    if iteration_count >= max_iterations:
        print(f"Max iterations ({max_iterations}) reached. Final score: {quality_score}/10")
        return "finalise"

    # Exercise 3: Route based on lowest score reaching threshold
    if quality_score >= quality_threshold and iteration_count > 0:
        print(f"✅ Quality threshold ({quality_threshold}) reached! Lowest score: {quality_score}/10")
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

    print("Starting multi-criteria iterative optimisation...")
    result = workflow.invoke({"input": task})
    
    # Display final results
    final_scores = {
        "Security": result.get("security_score", "N/A"),
        "Performance": result.get("performance_score", "N/A"),
        "Readability": result.get("readability_score", "N/A")
    }
    
    print(f"\n🏁 Final Scores:")
    for criteria, score in final_scores.items():
        print(f"  {criteria}: {score}/10")
    
    print(f"🎯 Lowest Score (routing basis): {result.get('lowest_score', 'N/A')}/10")
    print(f"🔄 Total Iterations: {result.get('iteration_count', 0)}")
    
    if result.get("fast_track"):
        print(f"🚀 Fast track was used - optimization skipped!")

    codebase = EvaluatorCodebase("05_evaluator_optimiser", task)
    codebase.generate(result)

    print("=== MULTI-CRITERIA OPTIMIZATION COMPLETED ===")
