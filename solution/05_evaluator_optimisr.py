from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Literal
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()


class Evaluation(BaseModel):
    overall_score: int = Field(
        description="Overall code quality score from 1-10")
    security_score: int = Field(description="Security score from 1-10")
    performance_score: int = Field(description="Performance score from 1-10")
    maintainability_score: int = Field(
        description="Maintainability score from 1-10")
    feedback: str = Field(description="Specific feedback for improvement")
    priority_issues: list[str] = Field(
        description="List of high priority issues to address")
    should_continue: bool = Field(
        description="Whether another iteration is needed")


class OptimisationState(TypedDict):
    input: str
    code: str
    evaluation_history: list
    current_evaluation: dict
    iteration_count: int
    improvement_log: str
    final_code: str


llm = ChatOpenAI(model="gpt-4o")

generator_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a Senior Software Engineer. Write production-quality Python code.

Previous feedback: {feedback}
Focus on: {priority_issues}"""),
    ("human", "{input}")
])

evaluator_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a Code Quality Evaluator. Assess code on multiple dimensions:

1. Security (1-10): Input validation, authentication, data protection
2. Performance (1-10): Algorithmic efficiency, resource usage, scalability
3. Maintainability (1-10): Code structure, readability, documentation

Provide specific, actionable feedback. A score of 8+ in all areas suggests completion."""),
    ("human", "Evaluate this code:\n{code}")
])

optimiser_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a Code Optimiser. Improve code based on specific feedback.

Previous evaluation: {evaluation}
Priority issues: {priority_issues}

Focus ONLY on the highlighted issues. Don't make unnecessary changes."""),
    ("human", "Optimise this code:\n{code}")
])


def code_generator(state: OptimisationState) -> OptimisationState:
    feedback = ""
    priority_issues = ""

    if state.get("current_evaluation"):
        feedback = state["current_evaluation"].get("feedback", "")
        priority_issues = ", ".join(
            state["current_evaluation"].get("priority_issues", []))

    response = llm.invoke(generator_prompt.format_messages(
        input=state["input"],
        feedback=feedback,
        priority_issues=priority_issues
    ))

    return {"code": response.content, "iteration_count": state.get("iteration_count", 0)}


def evaluator_agent(state: OptimisationState) -> OptimisationState:
    structured_llm = llm.with_structured_output(Evaluation)
    response = structured_llm.invoke(
        evaluator_prompt.format_messages(code=state["code"]))

    evaluation_history = state.get("evaluation_history", [])
    evaluation_dict = {
        "iteration": state.get("iteration_count", 0),
        "overall_score": response.overall_score,
        "security_score": response.security_score,
        "performance_score": response.performance_score,
        "maintainability_score": response.maintainability_score,
        "feedback": response.feedback,
        "priority_issues": response.priority_issues,
        "should_continue": response.should_continue
    }
    evaluation_history.append(evaluation_dict)

    return {
        "current_evaluation": evaluation_dict,
        "evaluation_history": evaluation_history
    }


def optimiser_agent(state: OptimisationState) -> OptimisationState:
    current_eval = state["current_evaluation"]

    response = llm.invoke(optimiser_prompt.format_messages(
        code=state["code"],
        evaluation=current_eval["feedback"],
        priority_issues=", ".join(current_eval["priority_issues"])
    ))

    improvement_log = state.get("improvement_log", "")
    new_log = f"Iteration {state['iteration_count']}: {current_eval['feedback'][:100]}...\n"

    return {
        "code": response.content,
        "iteration_count": state["iteration_count"] + 1,
        "improvement_log": improvement_log + new_log
    }


def finalise_code(state: OptimisationState) -> OptimisationState:
    return {"final_code": state["code"]}


def should_continue_optimisation(state: OptimisationState) -> Literal["optimise", "finalise"]:
    current_eval = state.get("current_evaluation", {})
    iteration_count = state.get("iteration_count", 0)

    max_iterations = 5
    quality_threshold = 8

    if iteration_count >= max_iterations:
        print(f"Max iterations ({max_iterations}) reached")
        return "finalise"

    if not current_eval.get("should_continue", True):
        print("Evaluator determined optimisation complete")
        return "finalise"

    overall_score = current_eval.get("overall_score", 0)
    if overall_score >= quality_threshold:
        print(
            f"Quality threshold ({quality_threshold}) reached with score {overall_score}")
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
    {
        "optimise": "optimiser",
        "finalise": "finalise"
    }
)
builder.add_edge("optimiser", "evaluator")
builder.add_edge("finalise", END)

workflow = builder.compile()

if __name__ == "__main__":
    task = "Write a REST API endpoint for file upload with validation and virus scanning"

    print("Starting iterative optimisation...")
    result = workflow.invoke({"input": task})

    print("=== OPTIMIsATION HISTORY ===")
    for i, eval_data in enumerate(result["evaluation_history"]):
        print(f"Iteration {eval_data['iteration']}:")
        print(f"  Overall: {eval_data['overall_score']}/10")
        print(f"  Security: {eval_data['security_score']}/10")
        print(f"  Performance: {eval_data['performance_score']}/10")
        print(f"  Maintainability: {eval_data['maintainability_score']}/10")
        print(f"  Issues: {eval_data['priority_issues']}")
        print()

    print("=== IMPROVEMENT LOG ===")
    print(result["improvement_log"])

    print("=== FINAL CODE ===")
    print(result["final_code"])

    print("=== EXERCISE ===")
    print("1. Add specific evaluation criteria (e.g., test coverage)")
    print("2. Create different optimisation strategies based on issue type")
    print("3. Add human-in-the-loop evaluation")
    print("4. When is iterative optimisation most valuable?")
