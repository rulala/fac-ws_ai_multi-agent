from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Literal
from dotenv import load_dotenv
from utils import ConditionalCodebase

load_dotenv()


class CodeReviewState(TypedDict):
    input: str
    code: list
    review: str
    security_score: int
    performance_score: int
    readability_score: int
    lowest_score: int
    iteration_count: int


llm = ChatOpenAI(model="gpt-4.1-nano")

coder_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a Senior Software Engineer. Write clean Python code."),
    ("human", "{input}")
])

reviewer_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a Code Reviewer. Provide feedback on code quality and best practices. In your review, comment on security, performance, and readability."),
    ("human", "Review this code:\n{code}")
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

refactorer_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a Refactoring Expert. Improve the code based on review feedback, focusing on the weakest area."),
    ("human",
     "Code:\n{code}\n\nFeedback:\n{review}\n\nScores - Security: {security}, Performance: {performance}, Readability: {readability}\n\nRefactor to address the lowest scoring area:")
])


def coder_agent(state: CodeReviewState) -> CodeReviewState:
    response = llm.invoke(coder_prompt.format_messages(input=state["input"]))
    return {"code": [response.content], "iteration_count": state.get("iteration_count", 0)}


def reviewer_agent(state: CodeReviewState) -> CodeReviewState:
    current_code = state["code"][-1] if state["code"] else ""
    response = llm.invoke(reviewer_prompt.format_messages(code=current_code))
    return {"review": response.content}


def multi_criteria_evaluator_agent(state: CodeReviewState) -> CodeReviewState:
    current_code = state["code"][-1] if state["code"] else ""

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

    return {
        "security_score": security_score,
        "performance_score": performance_score,
        "readability_score": readability_score,
        "lowest_score": lowest_score
    }


def refactorer_agent(state: CodeReviewState) -> CodeReviewState:
    current_code = state["code"][-1] if state["code"] else ""
    response = llm.invoke(refactorer_prompt.format_messages(
        code=current_code,
        review=state["review"],
        security=state["security_score"],
        performance=state["performance_score"],
        readability=state["readability_score"]
    ))
    updated_code_list = state["code"] + [response.content]
    return {
        "code": updated_code_list,
        "iteration_count": state["iteration_count"] + 1
    }


def quality_gate(state: CodeReviewState) -> Literal["refactor", "complete"]:
    quality_threshold = 7
    fast_track_threshold = 9
    max_iterations = 3

    if state["lowest_score"] >= fast_track_threshold and state["iteration_count"] == 0:
        print(
            f"🚀 Fast track activated! All scores ≥ {fast_track_threshold} - skipping refactoring entirely")
        return "complete"
    elif state["lowest_score"] >= quality_threshold:
        print(
            f"✅ All criteria passed! Lowest score: {state['lowest_score']}/10")
        return "complete"
    elif state["iteration_count"] >= max_iterations:
        print(f"Max iterations reached. Lowest score: {state['lowest_score']}")
        return "complete"
    else:
        return "refactor"


builder = StateGraph(CodeReviewState)
builder.add_node("coder", coder_agent)
builder.add_node("reviewer", reviewer_agent)
builder.add_node("multi_criteria_evaluator", multi_criteria_evaluator_agent)
builder.add_node("refactorer", refactorer_agent)

builder.add_edge(START, "coder")
builder.add_edge("coder", "reviewer")
builder.add_edge("reviewer", "multi_criteria_evaluator")
builder.add_conditional_edges(
    "multi_criteria_evaluator",
    quality_gate,
    {"refactor": "refactorer", "complete": END}
)
builder.add_edge("refactorer", "reviewer")

workflow = builder.compile()

workflow = builder.compile()

if __name__ == "__main__":
    task = "Write a function that processes user data with error handling"

    print("Running conditional routing...")
    result = workflow.invoke({"input": task})

    codebase = ConditionalCodebase("02_conditional_routing", task)
    codebase.generate(result)

    print("=== WORKFLOW COMPLETED ===")
