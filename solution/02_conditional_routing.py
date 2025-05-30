from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Literal
from dotenv import load_dotenv

load_dotenv()


class CodeReviewState(TypedDict):
    input: str
    code: str
    review: str
    quality_score: int
    iteration_count: int


llm = ChatOpenAI(model="gpt-4.1-nano")

coder_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a Senior Software Engineer. Write clean Python code."),
    ("human", "{input}")
])

reviewer_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a Code Reviewer. Provide feedback on code quality and best practices."),
    ("human", "Review this code:\n{code}")
])

evaluator_prompt = ChatPromptTemplate.from_messages([
    ("system", "Rate this code from 1-10 based on quality. Respond with just the number."),
    ("human", "Code:\n{code}\n\nReview:\n{review}")
])

refactorer_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a Refactoring Expert. Improve the code based on review feedback."),
    ("human", "Code:\n{code}\n\nFeedback:\n{review}\n\nRefactor to address issues:")
])


def coder_agent(state: CodeReviewState) -> CodeReviewState:
    response = llm.invoke(coder_prompt.format_messages(input=state["input"]))
    return {"code": response.content, "iteration_count": state.get("iteration_count", 0)}


def reviewer_agent(state: CodeReviewState) -> CodeReviewState:
    response = llm.invoke(reviewer_prompt.format_messages(code=state["code"]))
    return {"review": response.content}


def quality_evaluator_agent(state: CodeReviewState) -> CodeReviewState:
    response = llm.invoke(evaluator_prompt.format_messages(
        code=state["code"], review=state["review"]
    ))
    try:
        score = int(response.content.strip())
    except:
        score = 5
    return {"quality_score": score}


def refactorer_agent(state: CodeReviewState) -> CodeReviewState:
    response = llm.invoke(refactorer_prompt.format_messages(
        code=state["code"], review=state["review"]
    ))
    return {
        "code": response.content,
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
    {"refactor": "refactorer", "complete": END}
)
builder.add_edge("refactorer", "reviewer")

workflow = builder.compile()

if __name__ == "__main__":
    task = "Write a function that processes user data with error handling"

    print("Running conditional routing...")
    result = workflow.invoke({"input": task})

    print(f"=== FINAL CODE (Score: {result['quality_score']}, Iterations: {result['iteration_count']}) ===")
    print(result["code"])
    print("\n=== FINAL REVIEW ===")
    print(result["review"])