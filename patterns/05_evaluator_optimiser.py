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
    score: int
    scores: list
    iteration_count: int
    final_code: str


llm = ChatOpenAI(model="gpt-4.1-nano")

generator_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a Senior Software Engineer. Write ONLY Python code - no bash commands, no installation instructions, just the Python implementation."),
    ("human", "{input}")
])

evaluator_prompt = ChatPromptTemplate.from_messages([
    ("system", "Rate this code quality from 1-10. Consider security, performance, and readability. Respond with just the number."),
    ("human", "Code:\n{code}")
])

optimiser_prompt = ChatPromptTemplate.from_messages([
    ("system", "Improve this code based on quality concerns. Focus on security, performance, and readability."),
    ("human", "Code:\n{code}")
])


def code_generator(state: OptimisationState) -> OptimisationState:
    response = llm.invoke(
        generator_prompt.format_messages(input=state["input"]))
    return {"code": [response.content], "iteration_count": 0, "quality_scores": []}


def quality_evaluator_agent(state: OptimisationState) -> OptimisationState:
    current_code = state["code"][-1] if state["code"] else ""

    response = llm.invoke(evaluator_prompt.format_messages(code=current_code))

    try:
        score = int(response.content.strip())
    except:
        score = 5

    print(f"📊 Quality score: {score}/10")

    # Add score to history
    quality_scores = state.get("quality_scores", [])
    quality_scores.append(score)

    return {"quality_score": score, "quality_scores": quality_scores}


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
    quality_threshold = 7
    max_iterations = 3

    iteration_count = state.get("iteration_count", 0)
    quality_score = state.get("quality_score", 0)

    if iteration_count >= max_iterations:
        print(f"Max iterations reached. Final score: {quality_score}/10")
        return "finalise"

    if quality_score >= quality_threshold and iteration_count > 0:
        print(f"✅ Quality threshold reached! Score: {quality_score}/10")
        return "finalise"

    return "optimise"


builder = StateGraph(OptimisationState)
builder.add_node("generator", code_generator)
builder.add_node("evaluator", quality_evaluator_agent)
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
    task = "Write a REST API endpoint for file upload with validation"

    print("Starting iterative optimisation...")
    result = workflow.invoke({"input": task})

    codebase = EvaluatorCodebase("05_evaluator_optimiser", task)
    codebase.generate(result)

    print("=== EVALUATOR=OPTIMISER WORKFLOW COMPLETED ===")
