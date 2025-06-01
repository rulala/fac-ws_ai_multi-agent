from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Literal
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from utils import EvaluatorCodebase

load_dotenv()


class Evaluation(BaseModel):
    score: int = Field(description="Quality score from 1-10")
    feedback: str = Field(description="Specific improvement suggestions")
    should_continue: bool = Field(
        description="Whether another iteration is needed")


class OptimisationState(TypedDict):
    input: str
    code: str
    current_evaluation: dict
    iteration_count: int
    final_code: str


llm = ChatOpenAI(model="gpt-4.1-nano")

generator_prompt = ChatPromptTemplate.from_messages([
    ("system",
     "You are a Senior Software Engineer. Write ONLY Python code - no bash commands, no installation instructions, just the Python implementation. {feedback}"),
    ("human", "{input}")
])

evaluator_prompt = ChatPromptTemplate.from_messages([
    ("system", "Score code quality 1-10. Score 8+ suggests completion."),
    ("human", "Evaluate this code:\n{code}")
])

optimiser_prompt = ChatPromptTemplate.from_messages([
    ("system", "Improve code based on feedback: {feedback}"),
    ("human", "Optimise this code:\n{code}")
])


def code_generator(state: OptimisationState) -> OptimisationState:
    feedback = ""
    if state.get("current_evaluation"):
        feedback = f"Previous feedback: {state['current_evaluation']['feedback']}"

    response = llm.invoke(generator_prompt.format_messages(
        input=state["input"], feedback=feedback
    ))

    return {"code": response.content, "iteration_count": state.get("iteration_count", 0)}


def evaluator_agent(state: OptimisationState) -> OptimisationState:
    structured_llm = llm.with_structured_output(Evaluation)
    response = structured_llm.invoke(
        evaluator_prompt.format_messages(code=state["code"]))

    evaluation_dict = {
        "score": response.score,
        "feedback": response.feedback,
        "should_continue": response.should_continue
    }

    return {"current_evaluation": evaluation_dict}


def optimiser_agent(state: OptimisationState) -> OptimisationState:
    current_eval = state["current_evaluation"]

    response = llm.invoke(optimiser_prompt.format_messages(
        code=state["code"], feedback=current_eval["feedback"]
    ))

    return {
        "code": response.content,
        "iteration_count": state["iteration_count"] + 1
    }


def finalise_code(state: OptimisationState) -> OptimisationState:
    return {"final_code": state["code"]}


def should_continue_optimisation(state: OptimisationState) -> Literal["optimise", "finalise"]:
    current_eval = state.get("current_evaluation", {})
    iteration_count = state.get("iteration_count", 0)

    if iteration_count >= 3:
        return "finalise"

    if not current_eval.get("should_continue", True):
        return "finalise"

    if current_eval.get("score", 0) >= 8:
        return "finalise"

    return "optimise"


builder = StateGraph(OptimisationState)
builder.add_node("generator", code_generator)
builder.add_node("evaluator", evaluator_agent)
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

    print("=== WORKFLOW COMPLETED ===")
