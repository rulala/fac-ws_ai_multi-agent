from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Literal
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from utils import EvaluatorCodebase
import tempfile
import os
import matplotlib.pyplot as plt
import re

load_dotenv()


class Evaluation(BaseModel):
    quality_score: int = Field(description="Quality score from 1-10")
    complexity_score: int = Field(
        description="Complexity score from 1-10 (10 = simple)")
    feedback: str = Field(description="Specific improvement suggestions")
    should_continue: bool = Field(
        description="Whether another iteration is needed")


class OptimisationState(TypedDict):
    input: str
    code: str
    current_evaluation: dict
    iteration_count: int
    final_code: str
    history: list
    plateau_count: int
    performance_focused: bool


llm = ChatOpenAI(model="gpt-4.1-nano")

generator_prompt = ChatPromptTemplate.from_messages([
    ("system",
     "You are a Senior Software Engineer. Write ONLY Python code - no bash commands, no installation instructions, just the Python implementation. {feedback}"),
    ("human", "{input}")
])

evaluator_prompt = ChatPromptTemplate.from_messages([
    ("system", "Evaluate code on quality (1-10) and simplicity/low complexity (1-10). Quality score 8+ and complexity score 7+ suggests completion."),
    ("human", "Evaluate this code:\n{code}")
])

general_optimiser_prompt = ChatPromptTemplate.from_messages([
    ("system",
     "Improve code based on feedback focusing on quality and simplicity: {feedback}"),
    ("human", "Optimise this code:\n{code}")
])

performance_optimiser_prompt = ChatPromptTemplate.from_messages([
    ("system",
     "Improve code performance and efficiency based on feedback: {feedback}"),
    ("human", "Optimise this code for performance:\n{code}")
])


def calculate_complexity_score(code: str) -> int:
    try:
        import radon.complexity as radon_cc
        import radon.raw as radon_raw

        # Extract actual Python code from markdown blocks
        clean_code = extract_code_from_response(code)
        if not clean_code:
            clean_code = code

        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(clean_code)
            temp_path = f.name

        try:
            complexity = radon_cc.cc_visit(clean_code)
            raw_metrics = radon_raw.analyze(clean_code)

            avg_complexity = sum(
                block.complexity for block in complexity) / max(len(complexity), 1)
            loc = raw_metrics.loc

            if avg_complexity <= 2 and loc <= 20:
                return 10
            elif avg_complexity <= 4 and loc <= 50:
                return 8
            elif avg_complexity <= 6 and loc <= 100:
                return 6
            elif avg_complexity <= 8:
                return 4
            else:
                return 2
        finally:
            os.unlink(temp_path)

    except ImportError:
        clean_code = extract_code_from_response(code)
        if not clean_code:
            clean_code = code
        lines = len(clean_code.strip().split('\n'))
        if lines <= 20:
            return 10
        elif lines <= 50:
            return 8
        elif lines <= 100:
            return 6
        else:
            return 4


def extract_code_from_response(response_text: str) -> str:
    if not response_text:
        return ""

    code_block_pattern = r'```(?:python)?\s*(.*?)\s*```'
    match = re.search(code_block_pattern, response_text, re.DOTALL)
    return match.group(1).strip() if match else response_text.strip()


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

    complexity_score = calculate_complexity_score(state["code"])

    evaluation_dict = {
        "quality_score": response.quality_score,
        "complexity_score": complexity_score,
        "feedback": response.feedback,
        "should_continue": response.should_continue
    }

    performance_focused = "performance" in response.feedback.lower()

    history = state.get("history", [])
    history.append({
        "iteration": state.get("iteration_count", 0),
        "quality_score": response.quality_score,
        "complexity_score": complexity_score,
        "combined_score": (response.quality_score + complexity_score) / 2
    })

    plateau_count = 0
    if len(history) >= 3:
        recent_scores = [h["combined_score"] for h in history[-3:]]
        if max(recent_scores) - min(recent_scores) <= 0.5:
            plateau_count = state.get("plateau_count", 0) + 1

    return {
        "current_evaluation": evaluation_dict,
        "history": history,
        "plateau_count": plateau_count,
        "performance_focused": performance_focused
    }


def optimiser_agent(state: OptimisationState) -> OptimisationState:
    current_eval = state["current_evaluation"]
    performance_focused = state.get("performance_focused", False)

    if performance_focused:
        prompt = performance_optimiser_prompt
    else:
        prompt = general_optimiser_prompt

    response = llm.invoke(prompt.format_messages(
        code=state["code"], feedback=current_eval["feedback"]
    ))

    return {
        "code": response.content,
        "iteration_count": state["iteration_count"] + 1
    }


def finalise_code(state: OptimisationState) -> OptimisationState:
    history = state.get("history", [])

    if len(history) > 1:
        plt.figure(figsize=(10, 6))
        iterations = [h["iteration"] for h in history]
        quality_scores = [h["quality_score"] for h in history]
        complexity_scores = [h["complexity_score"] for h in history]
        combined_scores = [h["combined_score"] for h in history]

        plt.plot(iterations, quality_scores, 'b-o', label='Quality Score')
        plt.plot(iterations, complexity_scores,
                 'g-s', label='Complexity Score')
        plt.plot(iterations, combined_scores, 'r-^', label='Combined Score')

        plt.xlabel('Iteration')
        plt.ylabel('Score')
        plt.title('Code Optimisation Progress')
        plt.legend()
        plt.grid(True)
        plt.ylim(0, 11)

        chart_path = "optimisation_progress.png"
        plt.savefig(chart_path)
        plt.close()

        print(f"Progress chart saved to {chart_path}")

    return {"final_code": state["code"]}


def should_continue_optimisation(state: OptimisationState) -> Literal["optimise", "finalise"]:
    current_eval = state.get("current_evaluation", {})
    iteration_count = state.get("iteration_count", 0)
    plateau_count = state.get("plateau_count", 0)

    if iteration_count >= 3:
        return "finalise"

    if plateau_count >= 2:
        print("Plateau detected - stopping early")
        return "finalise"

    if not current_eval.get("should_continue", True):
        return "finalise"

    quality_score = current_eval.get("quality_score", 0)
    complexity_score = current_eval.get("complexity_score", 0)

    if quality_score >= 8 and complexity_score >= 7:
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
