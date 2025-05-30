from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Literal
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()


class QualityScore(BaseModel):
    score: int = Field(description="Quality score from 1-10")
    reasoning: str = Field(description="Explanation for the score")


class CodeReviewState(TypedDict):
    input: str
    code: str
    review: str
    refactored_code: str
    quality_score: int
    iteration_count: int


llm = ChatOpenAI(model="gpt-4o")

coder_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a Senior Software Engineer. Write clean, well-structured Python code."),
    ("human", "{input}")
])

reviewer_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a Code Reviewer. Provide detailed feedback on code quality, readability, and best practices."),
    ("human", "Review this code:\n{code}")
])

quality_evaluator_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a Quality Assessor. Score code from 1-10 based on readability, efficiency, and best practices."),
    ("human", "Code:\n{code}\n\nReview:\n{review}")
])

refactorer_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a Refactoring Expert. Focus on the specific issues mentioned in the review."),
    ("human",
     "Code:\n{code}\n\nReview feedback:\n{review}\n\nRefactor to address these issues:")
])


def coder_agent(state: CodeReviewState) -> CodeReviewState:
    response = llm.invoke(coder_prompt.format_messages(input=state["input"]))
    return {"code": response.content, "iteration_count": state.get("iteration_count", 0)}


def reviewer_agent(state: CodeReviewState) -> CodeReviewState:
    response = llm.invoke(reviewer_prompt.format_messages(code=state["code"]))
    return {"review": response.content}


def quality_evaluator_agent(state: CodeReviewState) -> CodeReviewState:
    structured_llm = llm.with_structured_output(QualityScore)
    response = structured_llm.invoke(quality_evaluator_prompt.format_messages(
        code=state["code"], review=state["review"]))
    return {"quality_score": response.score}


def refactorer_agent(state: CodeReviewState) -> CodeReviewState:
    response = llm.invoke(refactorer_prompt.format_messages(
        code=state["code"], review=state["review"]))
    return {
        "code": response.content,
        "refactored_code": response.content,
        "iteration_count": state["iteration_count"] + 1
    }


def quality_gate(state: CodeReviewState) -> Literal["refactor", "complete"]:
    quality_threshold = 7
    max_iterations = 3

    if state["quality_score"] >= quality_threshold:
        return "complete"
    elif state["iteration_count"] >= max_iterations:
        print(f"Max iterations reached. Final score: {state['quality_score']}")
        return "complete"
    else:
        return "refactor"


builder = StateGraph(CodeReviewState)
builder.add_node("coder", coder_agent)
builder.add_node("reviewer", reviewer_agent)
builder.add_node("quality_evaluator", quality_evaluator_agent)
builder.add_node("refactorer", refactorer_agent)

builder.add_edge(START, "coder")
builder.add_edge("coder", "reviewer")
builder.add_edge("reviewer", "quality_evaluator")
builder.add_conditional_edges(
    "quality_evaluator",
    quality_gate,
    {
        "refactor": "refactorer",
        "complete": END
    }
)
builder.add_edge("refactorer", "reviewer")

workflow = builder.compile()

if __name__ == "__main__":
    task = "Write a function that processes a list of user data and handles potential errors"

    result = workflow.invoke({"input": task})

    print(
        f"=== FINAL CODE (Score: {result['quality_score']}, Iterations: {result['iteration_count']}) ===")
    print(result["code"])
    print("\n=== FINAL REVIEW ===")
    print(result["review"])

    print("\n=== EXERCISE ===")
    print("1. Adjust quality threshold and see how it affects iterations")
    print("2. Add different quality criteria (security, performance)")
    print("3. Create a 'fast track' for simple code that skips some steps")
    print("4. When would conditional routing be better than sequential flow?")
